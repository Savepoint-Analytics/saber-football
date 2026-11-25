"""Build team, player, ID bridge, snap, and participation core tables."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, participation_source
from src.config import settings
from src.ingestion._storage import write_parquet
from src.warehouse.core import core_metadata_path, core_output_path
from src.warehouse.snapshots import Snapshot, read_build_inputs, read_manifest, read_snapshot

# Reviewed against same-game participation and roster or upstream identity evidence.
# See docs/nfl-data-review.md for the evidence and the intended alias semantics.
REVIEWED_SNAP_IDS = {
    "00-0035891": "WhitCo05",
    "00-0036093": "MurrBi00",
    "00-0037428": "AndeAl01",
    "00-0037451": "WillRo08",
    "00-0038658": "MartAd00",
    "00-0038920": "ShenJo00",
    "00-0039176": "OkoyCJ00",
    "00-0039245": "CoopBu00",
    "00-0039265": "HallGa01",
    "00-0039483": "JohnIs03",
    "00-0040317": "JoneJa16",
    "00-0040547": "CartNa00",
}


@dataclass(frozen=True)
class IdentityBuildResult:
    """Paths and row counts produced by identity/player-context builds."""

    season: int
    built_at_utc: str
    dim_team_path: str
    dim_team_rows: int
    dim_player_path: str
    dim_player_rows: int
    bridge_player_ids_path: str
    bridge_player_ids_rows: int
    fact_player_game_path: str
    fact_player_game_rows: int
    fact_player_on_play_path: str
    fact_player_on_play_rows: int
    raw_inputs: dict[str, Snapshot]


def identity_metadata_path(season: int) -> Path:
    return settings.data_dir / "core" / f"season={season}" / "identity_build_metadata.json"


def _json_struct(columns: list[str]) -> pl.Expr:
    return pl.struct(columns).map_elements(
        lambda row: json.dumps(
            {key: value for key, value in dict(row).items() if value not in (None, "")},
            sort_keys=True,
        ),
        return_dtype=pl.Utf8,
    )


def build_dim_team(teams: pl.DataFrame) -> pl.DataFrame:
    """Build dim_team from nflverse team metadata."""
    return (
        teams.filter(pl.col("team_abbr").is_not_null())
        .select(
            pl.col("team_abbr").cast(pl.Utf8).alias("team_id"),
            pl.lit("NFL").alias("league_id"),
            pl.col("team_name").cast(pl.Utf8),
            pl.col("team_abbr").cast(pl.Utf8),
            pl.lit(None).cast(pl.Utf8).alias("city"),
            pl.lit(None).cast(pl.Utf8).alias("state"),
            pl.col("team_conf").cast(pl.Utf8).alias("conference"),
            pl.col("team_division").cast(pl.Utf8).alias("division"),
            pl.lit(None).cast(pl.Int64).alias("active_from"),
            pl.lit(None).cast(pl.Int64).alias("active_to"),
            _json_struct(["team_id", "team_abbr"]).alias("source_team_ids"),
        )
        .unique(subset=["team_id"])
        .sort("team_id")
    )


def build_dim_player(players: pl.DataFrame) -> pl.DataFrame:
    """Build dim_player from nflverse players."""
    id_columns = [
        "gsis_id",
        "pfr_id",
        "pff_id",
        "otc_id",
        "espn_id",
        "esb_id",
        "nfl_id",
        "smart_id",
    ]
    return (
        players.filter(pl.col("gsis_id").is_not_null() & (pl.col("gsis_id") != ""))
        .select(
            pl.col("gsis_id").cast(pl.Utf8).alias("player_id"),
            pl.lit("NFL").alias("league_id"),
            pl.col("display_name").cast(pl.Utf8).alias("full_name"),
            pl.col("birth_date").cast(pl.Utf8),
            pl.col("height").cast(pl.Float64),
            pl.col("weight").cast(pl.Float64),
            pl.col("position").cast(pl.Utf8).alias("primary_position"),
            pl.col("college_name").cast(pl.Utf8).alias("college"),
            pl.lit(None).cast(pl.Utf8).alias("high_school"),
            _json_struct(id_columns).alias("source_ids_json"),
        )
        .unique(subset=["player_id"])
        .sort("player_id")
    )


def build_bridge_player_ids(players: pl.DataFrame) -> pl.DataFrame:
    """Build explicit player ID bridge across public football sources."""
    return (
        players.filter(pl.col("gsis_id").is_not_null() & (pl.col("gsis_id") != ""))
        .select(
            pl.col("gsis_id").cast(pl.Utf8).alias("player_id"),
            pl.col("gsis_id").cast(pl.Utf8),
            pl.col("pfr_id").cast(pl.Utf8),
            pl.col("pff_id").cast(pl.Utf8),
            pl.col("otc_id").cast(pl.Utf8),
            pl.col("espn_id").cast(pl.Utf8),
            pl.col("esb_id").cast(pl.Utf8),
            pl.col("nfl_id").cast(pl.Utf8),
            pl.col("smart_id").cast(pl.Utf8),
            pl.col("gsis_id")
            .replace_strict(REVIEWED_SNAP_IDS, default=None, return_dtype=pl.String)
            .alias("snap_pfr_alias"),
        )
        .unique(subset=["player_id"])
        .sort("player_id")
    )


def snap_id_lookup(bridge: pl.DataFrame) -> pl.DataFrame:
    """Keep source PFR IDs and add corroborated aliases without duplicate mappings."""
    ids = bridge.select("player_id", "pfr_id")
    if "snap_pfr_alias" in bridge.columns:
        ids = pl.concat([ids, bridge.select("player_id", pl.col("snap_pfr_alias").alias("pfr_id"))])
    return ids.filter(pl.col("pfr_id").is_not_null() & (pl.col("pfr_id") != "")).unique()


def build_fact_player_game(
    snap_counts: pl.DataFrame, bridge_player_ids: pl.DataFrame
) -> pl.DataFrame:
    """Build initial player-game facts from PFR-sourced snap counts.

    This is a snap/opportunity proxy table. It is not a player grade.
    """
    bridge = snap_id_lookup(bridge_player_ids)
    return (
        snap_counts.join(
            bridge, left_on="pfr_player_id", right_on="pfr_id", how="left", validate="m:1"
        )
        .with_columns(
            pl.coalesce([pl.col("player_id"), pl.format("pfr:{}", pl.col("pfr_player_id"))]).alias(
                "player_id"
            )
        )
        .select(
            pl.col("game_id").cast(pl.Utf8),
            pl.col("player_id").cast(pl.Utf8),
            pl.col("team").cast(pl.Utf8).alias("team_id"),
            pl.col("position").cast(pl.Utf8),
            (
                pl.col("offense_snaps").fill_null(0)
                + pl.col("defense_snaps").fill_null(0)
                + pl.col("st_snaps").fill_null(0)
                > 0
            ).alias("active_flag"),
            pl.lit(None).cast(pl.Boolean).alias("starter_flag"),
            pl.lit(None).cast(pl.Utf8).alias("injury_status"),
            pl.col("offense_snaps").cast(pl.Float64).alias("snaps_offense"),
            pl.col("defense_snaps").cast(pl.Float64).alias("snaps_defense"),
            pl.col("st_snaps").cast(pl.Float64).alias("snaps_special_teams"),
            pl.lit(None).cast(pl.Utf8).alias("passing_stats_json"),
            pl.lit(None).cast(pl.Utf8).alias("rushing_stats_json"),
            pl.lit(None).cast(pl.Utf8).alias("receiving_stats_json"),
            pl.lit(None).cast(pl.Utf8).alias("defensive_stats_json"),
            pl.lit(None).cast(pl.Utf8).alias("special_teams_stats_json"),
            pl.lit(None).cast(pl.Utf8).alias("ngs_stats_json"),
        )
        .sort(["game_id", "team_id", "player_id"])
    )


def _participation_side(
    participation_with_play: pl.DataFrame,
    *,
    side: str,
    player_col: str,
    name_col: str,
    position_col: str,
    team_expr: pl.Expr,
    opponent_expr: pl.Expr,
    personnel_col: str,
) -> pl.DataFrame:
    return (
        participation_with_play.select(
            pl.col("nflverse_game_id").cast(pl.Utf8).alias("game_id"),
            pl.col("play_id").cast(pl.Int64),
            team_expr.cast(pl.Utf8).alias("team_id"),
            opponent_expr.cast(pl.Utf8).alias("opponent_team_id"),
            pl.lit(side).alias("side"),
            pl.col(player_col).fill_null("").str.split(";").alias("player_id"),
            pl.col(name_col).fill_null("").str.split(";").alias("player_name"),
            pl.col(position_col).fill_null("").str.split(";").alias("position"),
            pl.col(personnel_col).cast(pl.Utf8).alias("personnel_group"),
            pl.col("defenders_in_box").cast(pl.Float64),
            pl.col("number_of_pass_rushers").cast(pl.Float64).alias("pass_rushers"),
        )
        .explode(["player_id", "player_name", "position"], empty_as_null=True)
        .filter(pl.col("player_id").is_not_null() & (pl.col("player_id") != ""))
        .with_columns(
            pl.lit(None).cast(pl.Utf8).alias("role"),
            pl.lit(True).alias("snap_flag"),
            pl.lit("nflverse_participation").alias("source"),
        )
        .select(
            "game_id",
            "play_id",
            "player_id",
            "team_id",
            "opponent_team_id",
            "side",
            "position",
            "role",
            "snap_flag",
            "personnel_group",
            "defenders_in_box",
            "pass_rushers",
            "source",
        )
    )


def build_fact_player_on_play(
    participation: pl.DataFrame, fact_play: pl.DataFrame, dim_game: pl.DataFrame
) -> pl.DataFrame:
    """Build participation-based player-on-play rows.

    This table uses public participation strings and should be treated as an on-field
    context proxy, not as assignment/charting truth.
    """
    play_context = fact_play.select(
        "game_id",
        "play_id",
        pl.col("posteam_id").alias("possession_team_from_pbp"),
        pl.col("defteam_id").alias("defteam_from_pbp"),
    )
    game_context = dim_game.select("game_id", "home_team_id", "away_team_id")
    participation_norm = participation.with_columns(pl.col("play_id").cast(pl.Int64))
    enriched = participation_norm.join(
        play_context,
        left_on=["nflverse_game_id", "play_id"],
        right_on=["game_id", "play_id"],
        how="left",
    ).join(game_context, left_on="nflverse_game_id", right_on="game_id", how="left")
    enriched = enriched.with_columns(
        pl.coalesce([pl.col("possession_team"), pl.col("possession_team_from_pbp")]).alias(
            "offense_team_id"
        )
    ).with_columns(
        pl.coalesce(
            [
                pl.col("defteam_from_pbp"),
                pl.when(pl.col("offense_team_id") == pl.col("home_team_id"))
                .then(pl.col("away_team_id"))
                .when(pl.col("offense_team_id") == pl.col("away_team_id"))
                .then(pl.col("home_team_id"))
                .otherwise(None),
            ]
        ).alias("defense_team_id")
    )

    offense = _participation_side(
        enriched,
        side="offense",
        player_col="offense_players",
        name_col="offense_names",
        position_col="offense_positions",
        team_expr=pl.col("offense_team_id"),
        opponent_expr=pl.col("defense_team_id"),
        personnel_col="offense_personnel",
    )
    defense = _participation_side(
        enriched,
        side="defense",
        player_col="defense_players",
        name_col="defense_names",
        position_col="defense_positions",
        team_expr=pl.col("defense_team_id"),
        opponent_expr=pl.col("offense_team_id"),
        personnel_col="defense_personnel",
    )
    rows = pl.concat([offense, defense], how="vertical")
    # A source lineup can list the same player twice with different position tags.
    # Keep a single participation record when the rest of the context agrees.
    positions = pl.col("position").replace("", None).drop_nulls()
    return (
        rows.group_by(pl.exclude("position"))
        .agg(pl.when(positions.n_unique() == 1).then(positions.first()).alias("position"))
        .select(rows.columns)
        .sort(["game_id", "play_id", "side", "player_id"])
    )


def identity_output_path(table: str, season: int | None = None) -> Path:
    """Return output path for identity/player-context core tables."""
    if season is None:
        return settings.data_dir / "core" / table / "league=nfl" / f"{table}.parquet"
    return (
        settings.data_dir / "core" / table / "league=nfl" / f"season={season}" / f"{table}.parquet"
    )


def _write_table(
    frame: pl.DataFrame, table: str, *, season: int | None, sources: list[Source]
) -> Path:
    path = identity_output_path(table, season)
    write_parquet(frame, path, sources=sources)
    return path


def build_identity_tables(season: int, manifest: Path | None = None) -> IdentityBuildResult:
    """Build identity and player-context tables from raw nflverse snapshots."""
    pins = read_manifest(manifest, season)
    core_inputs = read_build_inputs(core_metadata_path(season), season)
    if pins is not None:
        for dataset in ("nflverse_schedules", "nflverse_pbp"):
            if core_inputs is None or core_inputs[dataset].sha256 != pins[dataset].sha256:
                raise ValueError("core inputs differ from the manifest; rebuild core first")
    teams, teams_input = read_snapshot("nflverse_teams", None, pins)
    players, players_input = read_snapshot("nflverse_players", None, pins)
    snap_counts, snap_input = read_snapshot("nflverse_snap_counts", season, pins)
    participation, participation_input = read_snapshot("nflverse_participation", season, pins)
    fact_play = pl.read_parquet(core_output_path("fact_play", season))
    dim_game = pl.read_parquet(core_output_path("dim_game", season))

    dim_team = build_dim_team(teams)
    dim_player = build_dim_player(players)
    bridge_player_ids = build_bridge_player_ids(players)
    fact_player_game = build_fact_player_game(snap_counts, bridge_player_ids)
    fact_player_on_play = build_fact_player_on_play(participation, fact_play, dim_game)

    dim_team_path = _write_table(dim_team, "dim_team", season=None, sources=[Source.NFLVERSE])
    dim_player_path = _write_table(dim_player, "dim_player", season=None, sources=[Source.NFLVERSE])
    bridge_path = _write_table(
        bridge_player_ids, "bridge_player_ids", season=None, sources=[Source.NFLVERSE]
    )
    fact_player_game_path = _write_table(
        fact_player_game, "fact_player_game", season=season, sources=[Source.NFLVERSE, Source.PFR]
    )
    fact_player_on_play_path = _write_table(
        fact_player_on_play,
        "fact_player_on_play",
        season=season,
        sources=[Source.NFLVERSE, participation_source(season)],
    )

    result = IdentityBuildResult(
        season=season,
        built_at_utc=datetime.now(UTC).isoformat(),
        dim_team_path=str(dim_team_path),
        dim_team_rows=dim_team.height,
        dim_player_path=str(dim_player_path),
        dim_player_rows=dim_player.height,
        bridge_player_ids_path=str(bridge_path),
        bridge_player_ids_rows=bridge_player_ids.height,
        fact_player_game_path=str(fact_player_game_path),
        fact_player_game_rows=fact_player_game.height,
        fact_player_on_play_path=str(fact_player_on_play_path),
        fact_player_on_play_rows=fact_player_on_play.height,
        raw_inputs={
            **(core_inputs or {}),
            "nflverse_teams": teams_input,
            "nflverse_players": players_input,
            "nflverse_snap_counts": snap_input,
            "nflverse_participation": participation_input,
        },
    )
    metadata_path = identity_metadata_path(season)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: `python -m src.warehouse.identity --season 2025`."""
    parser = argparse.ArgumentParser(description="Build identity/player-context core tables.")
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    result = build_identity_tables(args.season, args.manifest)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
