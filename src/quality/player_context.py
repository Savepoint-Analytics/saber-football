"""Audit player IDs, snap-count joins, and participation coverage."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, participation_source
from src.config import settings
from src.ingestion._storage import write_parquet
from src.warehouse.core import core_output_path
from src.warehouse.identity import identity_metadata_path, identity_output_path
from src.warehouse.snapshots import read_build_inputs, read_manifest, read_snapshot

TEAM_GAME = ["game_id", "team_id"]
PLAYER_GAME = [*TEAM_GAME, "player_id"]
PLAYER_PLAY = ["game_id", "play_id", "side", "player_id"]


def _key_issues(frame: pl.DataFrame, key: list[str]) -> dict[str, int]:
    return {
        "null_key_rows": frame.filter(pl.any_horizontal(pl.col(key).is_null())).height,
        "duplicate_key_rows": frame.height - frame.select(key).unique().height,
    }


def _rate(numerator: pl.Expr, denominator: pl.Expr) -> pl.Expr:
    return pl.when(denominator > 0).then(numerator / denominator)


def _name_key(column: str) -> pl.Expr:
    return pl.col(column).str.to_lowercase().str.replace_all(r"[^a-z0-9]", "")


def audit_snap_ids(
    raw_snaps: pl.DataFrame, bridge: pl.DataFrame, rosters: pl.DataFrame
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Classify source rows and attach candidate evidence for unresolved PFR IDs."""
    lookup = (
        bridge.filter(pl.col("pfr_id").is_not_null() & (pl.col("pfr_id") != ""))
        .group_by("pfr_id")
        .agg(pl.col("player_id").n_unique().alias("bridge_matches"))
    )
    snaps = (
        raw_snaps.rename({"team": "team_id", "pfr_player_id": "pfr_id"})
        .join(lookup, on="pfr_id", how="left")
        .with_columns(pl.col("bridge_matches").fill_null(0))
    )
    candidates = rosters.select(
        _name_key("full_name").alias("name_key"),
        pl.col("team").alias("team_id"),
        pl.col("gsis_id").alias("roster_gsis_id"),
        pl.col("pfr_id").alias("roster_pfr_id"),
    ).unique()
    review = (
        snaps.filter(pl.col("bridge_matches") != 1)
        .group_by("pfr_id", "player", "team_id", "position", "bridge_matches")
        .agg(pl.len().alias("snap_rows"), pl.col("game_id").unique().sort().alias("games"))
        .with_columns(_name_key("player").alias("name_key"))
        .join(candidates, on=["team_id", "name_key"], how="left")
        .drop("name_key")
        .with_columns(
            pl.when(pl.col("bridge_matches") > 1)
            .then(pl.lit("ambiguous_bridge_id"))
            .when(pl.col("roster_gsis_id").is_null())
            .then(pl.lit("no_same_team_roster_candidate"))
            .when(pl.col("roster_pfr_id") == pl.col("pfr_id"))
            .then(pl.lit("roster_id_match"))
            .when(pl.col("roster_pfr_id").is_not_null())
            .then(pl.lit("conflicting_roster_pfr_id"))
            .otherwise(pl.lit("roster_name_candidate"))
            .alias("review_status")
        )
        .sort(["pfr_id", "team_id", "roster_gsis_id", "roster_pfr_id"])
    )
    return snaps, review


def team_game_coverage(
    games: pl.DataFrame,
    plays: pl.DataFrame,
    snaps: pl.DataFrame,
    player_games: pl.DataFrame,
    participation: pl.DataFrame,
) -> pl.DataFrame:
    """Measure snap coverage and on-field coverage against scheduled teams and analysis plays."""
    teams = pl.concat(
        [
            games.select("game_id", "week", pl.col(team).alias("team_id"))
            for team in ("home_team_id", "away_team_id")
        ]
    )
    expected_plays = pl.concat(
        [
            plays.select(
                "game_id", "play_id", pl.col(team).alias("team_id"), pl.lit(side).alias("side")
            )
            for team, side in (("posteam_id", "offense"), ("defteam_id", "defense"))
        ]
    ).drop_nulls("team_id")
    lineups = participation.group_by(*TEAM_GAME, "play_id", "side").agg(
        pl.col("player_id").n_unique().alias("recorded_players")
    )
    coverage = (
        expected_plays.join(lineups, on=[*TEAM_GAME, "play_id", "side"], how="left")
        .group_by(TEAM_GAME)
        .agg(
            pl.len().alias("analysis_play_sides"),
            (pl.col("recorded_players").fill_null(0) > 0).sum().alias("covered_play_sides"),
            (pl.col("recorded_players") == 11).sum().alias("eleven_player_sides"),
        )
    )
    snap_summary = snaps.group_by(TEAM_GAME).agg(
        pl.len().alias("source_snap_rows"),
        (pl.col("bridge_matches") == 1).sum().alias("matched_snap_rows"),
    )
    player_summary = player_games.group_by(TEAM_GAME).len(name="fact_snap_rows")
    return (
        teams.join(coverage, on=TEAM_GAME, how="left")
        .join(snap_summary, on=TEAM_GAME, how="left")
        .join(player_summary, on=TEAM_GAME, how="left")
        .with_columns(pl.selectors.integer().exclude("week").fill_null(0))
        .with_columns(
            snap_id_match_rate=_rate(pl.col("matched_snap_rows"), pl.col("source_snap_rows")),
            participation_coverage_rate=_rate(
                pl.col("covered_play_sides"), pl.col("analysis_play_sides")
            ),
        )
        .sort(["week", *TEAM_GAME])
    )


def build_player_quality(season: int, manifest: Path | None = None) -> dict[str, object]:
    """Write detailed Parquet audits and a season-level summary."""
    identity_inputs = read_build_inputs(identity_metadata_path(season), season)
    pins = read_manifest(manifest, season)
    if identity_inputs is None:
        raise ValueError("rebuild identity before auditing player context")
    if pins is not None:
        for dataset, snapshot in identity_inputs.items():
            if pins[dataset].sha256 != snapshot.sha256:
                raise ValueError("identity inputs differ from the manifest; rebuild identity first")
    raw_snaps, _ = read_snapshot("nflverse_snap_counts", season, identity_inputs)
    rosters, roster_input = read_snapshot("nflverse_rosters", season, pins)
    games = pl.read_parquet(core_output_path("dim_game", season))
    plays = pl.read_parquet(core_output_path("fact_play", season))
    players = pl.read_parquet(identity_output_path("dim_player"))
    bridge = pl.read_parquet(identity_output_path("bridge_player_ids"))
    player_games = pl.read_parquet(identity_output_path("fact_player_game", season))
    participation = pl.read_parquet(identity_output_path("fact_player_on_play", season))

    snaps, review = audit_snap_ids(raw_snaps, bridge, rosters)
    coverage = team_game_coverage(games, plays, snaps, player_games, participation)
    keys = {
        "dim_team": _key_issues(pl.read_parquet(identity_output_path("dim_team")), ["team_id"]),
        "dim_player": _key_issues(players, ["player_id"]),
        "bridge_player_ids": _key_issues(bridge, ["player_id"]),
        "bridge_pfr_ids": _key_issues(
            bridge.filter(pl.col("pfr_id").is_not_null() & (pl.col("pfr_id") != "")), ["pfr_id"]
        ),
        "fact_player_game": _key_issues(player_games, PLAYER_GAME),
        "fact_player_on_play": _key_issues(participation, PLAYER_PLAY),
    }
    lookup = players.select("player_id")
    missing_snap_players = player_games.join(lookup, on="player_id", how="anti").height
    missing_participation_players = participation.join(lookup, on="player_id", how="anti").height
    scheduled = coverage.select(TEAM_GAME)
    unscheduled_player_games = player_games.join(scheduled, on=TEAM_GAME, how="anti").height
    unscheduled_participation = participation.join(scheduled, on=TEAM_GAME, how="anti").height
    snap_row_mismatches = coverage.filter(
        pl.col("source_snap_rows") != pl.col("fact_snap_rows")
    ).height
    source_snap_rows = raw_snaps.height
    matched_snap_rows = snaps.filter(pl.col("bridge_matches") == 1).height
    expected = int(coverage["analysis_play_sides"].sum())
    covered = int(coverage["covered_play_sides"].sum())

    output = settings.data_dir / "quality" / f"season={season}" / "player_context"
    write_parquet(
        coverage,
        output / "team_game_coverage.parquet",
        sources=[Source.NFLVERSE, Source.PFR, participation_source(season)],
    )
    write_parquet(
        review,
        output / "unresolved_snap_ids" / "unresolved_snap_ids.parquet",
        sources=[Source.NFLVERSE, Source.PFR],
    )
    summary: dict[str, object] = {
        "season": season,
        "claim_type": "descriptive",
        "raw_inputs": {
            **{dataset: asdict(snapshot) for dataset, snapshot in identity_inputs.items()},
            "nflverse_rosters": asdict(roster_input),
        },
        "keys": keys,
        "scheduled_games": games.height,
        "scheduled_team_games": coverage.height,
        "source_snap_rows": source_snap_rows,
        "matched_snap_rows": matched_snap_rows,
        "snap_id_match_rate": matched_snap_rows / source_snap_rows if source_snap_rows else None,
        "unresolved_pfr_ids": review["pfr_id"].n_unique(),
        "player_game_rows_missing_dim_player": missing_snap_players,
        "participation_rows_missing_dim_player": missing_participation_players,
        "unscheduled_player_game_rows": unscheduled_player_games,
        "unscheduled_participation_rows": unscheduled_participation,
        "team_games_with_snap_row_count_mismatch": snap_row_mismatches,
        "team_games_without_snap_rows": coverage.filter(pl.col("source_snap_rows") == 0).height,
        "team_games_without_analysis_plays": coverage.filter(
            pl.col("analysis_play_sides") == 0
        ).height,
        "team_games_without_covered_analysis_plays": coverage.filter(
            (pl.col("analysis_play_sides") > 0) & (pl.col("covered_play_sides") == 0)
        ).height,
        "participation_rows": participation.height,
        "expected_analysis_play_sides": expected,
        "covered_analysis_play_sides": covered,
        "participation_coverage_rate": covered / expected if expected else None,
        "eleven_player_analysis_play_sides": coverage["eleven_player_sides"].sum(),
        "structural_checks_passed": not (
            any(any(issues.values()) for issues in keys.values())
            or unscheduled_player_games
            or unscheduled_participation
            or snap_row_mismatches
            or player_games.height != source_snap_rows
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    summary = build_player_quality(args.season, args.manifest)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["structural_checks_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
