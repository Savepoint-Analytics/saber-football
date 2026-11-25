"""Build descriptive NFL player opportunity from PFR snaps and on-field participation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, participation_source
from src.config import settings
from src.ingestion._storage import write_parquet
from src.warehouse.core import core_output_path
from src.warehouse.identity import identity_metadata_path, identity_output_path, snap_id_lookup
from src.warehouse.snapshots import read_build_inputs, read_snapshot

PHASES = ("offense", "defense", "special_teams")
SIDES = ("offense", "defense")
TEAM_GAME = ["game_id", "team_id"]
PLAYER_GAME = [*TEAM_GAME, "player_id"]
ROLE_GROUPS = {
    "QB": ("QB",),
    "Backfield": ("RB", "FB", "HB"),
    "Receiver": ("WR",),
    "Tight end": ("TE",),
    "Offensive line": ("OL", "C", "G", "LG", "RG", "T", "LT", "RT", "OT", "OG", "OL/C"),
    "Defensive line": ("DL", "DT", "DE", "NT", "EDGE"),
    "Linebacker": ("LB", "ILB", "OLB", "MLB"),
    "Defensive back": ("DB", "CB", "S", "FS", "SS", "SAF"),
    "Specialist": ("K", "P", "LS"),
}
ROLE_BY_POSITION = {
    position: role for role, positions in ROLE_GROUPS.items() for position in positions
}


def _rate(numerator: pl.Expr, denominator: pl.Expr) -> pl.Expr:
    return pl.when(denominator > 0).then(numerator / denominator)


def exact_snap_total(rows: list[tuple[float | None, float | None]]) -> int | None:
    """Infer a team total only if one count fits all rounded whole-percent PFR shares."""
    observed = [
        (int(snaps), round(share * 100))
        for snaps, share in rows
        if snaps is not None and share is not None
    ]
    lower = max((int(snaps) for snaps, _ in rows if snaps is not None), default=0)
    upper = min((200 * snaps // (2 * pct - 1) for snaps, pct in observed if pct > 0), default=0)
    candidates = [
        total
        for total in range(max(1, lower), upper + 1)
        if all(2 * abs(100 * snaps - pct * total) <= total for snaps, pct in observed)
    ]
    return candidates[0] if len(candidates) == 1 else None


def _snap_inputs(raw: pl.DataFrame, bridge: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    denominators = pl.DataFrame(
        [
            {
                "game_id": game,
                "team_id": team,
                **{
                    f"{phase}_team_snaps": exact_snap_total(
                        rows.select(f"{column}_snaps", f"{column}_pct").rows()
                    )
                    for phase, column in zip(PHASES, ("offense", "defense", "st"), strict=True)
                },
            }
            for (game, team), rows in raw.group_by("game_id", "team")
        ],
        schema={
            "game_id": pl.String,
            "team_id": pl.String,
            **{f"{p}_team_snaps": pl.Int64 for p in PHASES},
        },
    )
    reports = raw.join(
        snap_id_lookup(bridge),
        left_on="pfr_player_id",
        right_on="pfr_id",
        how="left",
        validate="m:1",
    ).select(
        "game_id",
        pl.col("team").alias("team_id"),
        pl.coalesce("player_id", pl.format("pfr:{}", pl.col("pfr_player_id"))).alias("player_id"),
        pl.col("player").alias("source_name"),
        "offense_pct",
        "defense_pct",
        pl.col("st_pct").alias("special_teams_pct"),
    )
    return denominators, reports


def _participation_inputs(
    plays: pl.DataFrame, participation: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    expected = (
        pl.concat(
            [
                plays.select(
                    "game_id", "play_id", pl.col(team).alias("team_id"), pl.lit(side).alias("side")
                )
                for side, team in zip(SIDES, ("posteam_id", "defteam_id"), strict=True)
            ]
        )
        .drop_nulls("team_id")
        .unique()
    )
    play_key = [*TEAM_GAME, "play_id", "side"]
    recorded = participation.join(expected, on=play_key, how="semi")
    counts = recorded.group_by(PLAYER_GAME).agg(
        *[
            pl.col("play_id").filter(pl.col("side") == side).n_unique().alias(f"{side}_on_field")
            for side in SIDES
        ],
    )
    coverage = (
        expected.join(
            recorded.select(play_key).unique().with_columns(observed=pl.lit(True)),
            on=play_key,
            how="left",
        )
        .group_by(TEAM_GAME)
        .agg(
            *[
                expression
                for side in SIDES
                for expression in (
                    (pl.col("side") == side).sum().alias(f"{side}_expected_plays"),
                    ((pl.col("side") == side) & pl.col("observed").fill_null(False))
                    .sum()
                    .alias(f"{side}_covered_plays"),
                )
            ]
        )
    )
    return counts, coverage


def _league_team_games(games: pl.DataFrame) -> pl.DataFrame:
    return pl.concat(
        [
            games.filter(
                pl.col("home_score").is_not_null() & pl.col("away_score").is_not_null()
            ).select(
                "season",
                "week",
                "game_id",
                "season_type",
                pl.col(team).alias("team_id"),
                pl.col(opponent).alias("opponent_team_id"),
            )
            for team, opponent in (
                ("home_team_id", "away_team_id"),
                ("away_team_id", "home_team_id"),
            )
        ]
    )


def build_opportunity(
    games: pl.DataFrame,
    plays: pl.DataFrame,
    players: pl.DataFrame,
    bridge: pl.DataFrame,
    player_games: pl.DataFrame,
    participation: pl.DataFrame,
    raw_snaps: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return player/team/game and player/team/role/season opportunity tables."""
    schedule = _league_team_games(games)
    denominators, provider_shares = _snap_inputs(raw_snaps, bridge)
    counts, coverage = _participation_inputs(plays, participation)
    by_game = (
        player_games.select(
            PLAYER_GAME + ["position", "snaps_offense", "snaps_defense", "snaps_special_teams"]
        )
        .join(provider_shares, on=PLAYER_GAME, how="left", validate="1:1")
        .join(counts, on=PLAYER_GAME, how="full", coalesce=True, validate="1:1")
        .join(schedule, on=TEAM_GAME, how="inner", validate="m:1")
        .join(denominators, on=TEAM_GAME, how="left", validate="m:1")
        .join(coverage, on=TEAM_GAME, how="left", validate="m:1")
        .join(
            players.select("player_id", "full_name", "primary_position"),
            on="player_id",
            how="left",
            validate="m:1",
        )
        .with_columns(
            player=pl.coalesce("full_name", "source_name", "player_id"),
            role=pl.coalesce(pl.col("position").replace("", None), "primary_position")
            .str.to_uppercase()
            .fill_null("")
            .replace_strict(ROLE_BY_POSITION, default="Other", return_dtype=pl.String),
        )
        .with_columns(
            *[
                expression
                for phase in PHASES
                for expression in (
                    pl.coalesce(
                        _rate(pl.col(f"snaps_{phase}"), pl.col(f"{phase}_team_snaps")),
                        pl.col(f"{phase}_pct"),
                    ).alias(f"{phase}_snap_share"),
                    pl.when(
                        pl.col(f"{phase}_team_snaps").is_not_null()
                        & pl.col(f"snaps_{phase}").is_not_null()
                    )
                    .then(pl.lit("Reconstructed team total"))
                    .when(pl.col(f"{phase}_pct").is_not_null())
                    .then(pl.lit("PFR rounded share"))
                    .otherwise(pl.lit("Unavailable"))
                    .alias(f"{phase}_share_basis"),
                )
            ],
            *[
                pl.when(pl.col(f"{side}_covered_plays") > 0)
                .then(pl.col(f"{side}_on_field").fill_null(0))
                .alias(f"{side}_on_field")
                for side in SIDES
            ],
        )
        .drop(
            "position",
            "primary_position",
            "full_name",
            "source_name",
            *[f"{p}_pct" for p in PHASES],
        )
        .sort("week", "game_id", "team_id", "player_id")
    )
    exact = {
        phase: pl.col(f"{phase}_team_snaps").is_not_null() & pl.col(f"snaps_{phase}").is_not_null()
        for phase in PHASES
    }
    by_season = (
        by_game.group_by("season", "team_id", "role", "player_id")
        .agg(
            pl.col("player").first(),
            pl.len().alias("player_games"),
            *[
                expression
                for phase in PHASES
                for expression in (
                    pl.when(pl.col(f"snaps_{phase}").count() > 0)
                    .then(pl.col(f"snaps_{phase}").sum())
                    .alias(f"snaps_{phase}"),
                    pl.col(f"snaps_{phase}").count().alias(f"{phase}_snap_source_games"),
                    exact[phase].sum().alias(f"{phase}_share_games"),
                    pl.col(f"snaps_{phase}")
                    .filter(exact[phase])
                    .sum()
                    .alias(f"{phase}_share_snaps"),
                    pl.col(f"{phase}_team_snaps")
                    .filter(exact[phase])
                    .sum()
                    .alias(f"{phase}_team_snaps"),
                )
            ],
            *[
                expression
                for side in SIDES
                for expression in (
                    pl.when(pl.col(f"{side}_on_field").count() > 0)
                    .then(pl.col(f"{side}_on_field").sum())
                    .alias(f"{side}_on_field"),
                    pl.col(f"{side}_covered_plays").sum(),
                    pl.col(f"{side}_expected_plays").sum(),
                )
            ],
        )
        .join(
            schedule.group_by("season", "team_id").len(name="team_games"),
            on=["season", "team_id"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            *[
                _rate(pl.col(f"{phase}_share_snaps"), pl.col(f"{phase}_team_snaps")).alias(
                    f"{phase}_snap_share"
                )
                for phase in PHASES
            ]
        )
        .sort("team_id", "role", "player_id")
    )
    return by_game, by_season


def opportunity_path(table: str, season: int) -> Path:
    return (
        settings.data_dir
        / "analytics"
        / table
        / "league=nfl"
        / f"season={season}"
        / f"{table}.parquet"
    )


def write_opportunity(season: int) -> dict[str, object]:
    pins = read_build_inputs(identity_metadata_path(season), season)
    if pins is None:
        raise ValueError("rebuild identity before building player opportunity")
    snaps, _ = read_snapshot("nflverse_snap_counts", season, pins)
    game, season_view = build_opportunity(
        pl.read_parquet(core_output_path("dim_game", season)),
        pl.read_parquet(core_output_path("fact_play", season)),
        pl.read_parquet(identity_output_path("dim_player")),
        pl.read_parquet(identity_output_path("bridge_player_ids")),
        pl.read_parquet(identity_output_path("fact_player_game", season)),
        pl.read_parquet(identity_output_path("fact_player_on_play", season)),
        snaps,
    )
    artifacts = {}
    for table, frame in (
        ("player_game_opportunity", game),
        ("player_season_opportunity", season_view),
    ):
        path = opportunity_path(table, season)
        write_parquet(
            frame, path, sources=[Source.NFLVERSE, Source.PFR, participation_source(season)]
        )
        artifacts[table] = {"path": str(path), "rows": frame.height}
    metadata = {
        "season": season,
        "claim_type": "descriptive",
        "built_at_utc": datetime.now(UTC).isoformat(),
        "raw_inputs": {dataset: asdict(pin) for dataset, pin in pins.items()},
        "outputs": artifacts,
    }
    path = settings.data_dir / "analytics" / f"season={season}" / "player_opportunity_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", required=True, type=int)
    print(json.dumps(write_opportunity(parser.parse_args().season), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
