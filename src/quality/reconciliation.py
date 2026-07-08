"""Reconcile core EPA/WPA tables against raw nflverse aggregates."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, attribution_block
from src.config import settings
from src.warehouse.core import core_output_path, latest_raw_snapshot


@dataclass(frozen=True)
class ReconciliationResult:
    """Summary of an EPA/WPA reconciliation run."""

    season: int
    built_at_utc: str
    report_path: str
    rows: int
    max_abs_offensive_epa_diff: float
    max_abs_analysis_net_epa_diff: float
    max_abs_public_cumulative_epa_check_diff: float
    max_abs_wpa_diff: float
    max_abs_play_count_diff: int
    notes: str


def _raw_analysis_team_game(raw_pbp: pl.DataFrame) -> pl.DataFrame:
    non_special = pl.col("special_teams_play").fill_null(0) != 1
    return (
        raw_pbp.filter((pl.col("play").fill_null(0) == 1) & pl.col("posteam").is_not_null())
        .group_by(["game_id", "posteam"])
        .agg(
            pl.col("epa").filter(non_special).sum().alias("raw_analysis_offensive_epa"),
            pl.col("epa").filter(~non_special).sum().alias("raw_analysis_special_teams_epa"),
            pl.col("wpa").sum().alias("raw_analysis_wpa"),
            pl.len().alias("raw_analysis_plays"),
        )
        .rename({"posteam": "team_id"})
    )


def _raw_analysis_net(raw_analysis: pl.DataFrame, dim_game: pl.DataFrame) -> pl.DataFrame:
    team_rows = pl.concat(
        [
            dim_game.select(
                "game_id",
                pl.col("home_team_id").alias("team_id"),
                pl.col("away_team_id").alias("opponent_team_id"),
            ),
            dim_game.select(
                "game_id",
                pl.col("away_team_id").alias("team_id"),
                pl.col("home_team_id").alias("opponent_team_id"),
            ),
        ],
        how="vertical",
    )
    return (
        team_rows.join(raw_analysis, on=["game_id", "team_id"], how="left")
        .join(
            raw_analysis.select(
                "game_id",
                pl.col("team_id").alias("opponent_team_id"),
                pl.col("raw_analysis_offensive_epa").alias("raw_opponent_analysis_epa"),
            ),
            on=["game_id", "opponent_team_id"],
            how="left",
        )
        .with_columns(
            (
                pl.col("raw_analysis_offensive_epa").fill_null(0.0)
                + pl.col("raw_analysis_special_teams_epa").fill_null(0.0)
                - pl.col("raw_opponent_analysis_epa").fill_null(0.0)
            ).alias("raw_analysis_net_epa")
        )
        .select(["game_id", "team_id", "raw_analysis_net_epa"])
    )


def _public_cumulative_net(raw_pbp: pl.DataFrame) -> pl.DataFrame:
    final = raw_pbp.sort(["game_id", "play_id"]).group_by("game_id").tail(1)
    home = final.select(
        "game_id",
        pl.col("home_team").alias("team_id"),
        pl.col("total_home_epa").alias("public_cumulative_net_epa"),
    )
    away = final.select(
        "game_id",
        pl.col("away_team").alias("team_id"),
        pl.col("total_away_epa").alias("public_cumulative_net_epa"),
    )
    return pl.concat([home, away], how="vertical")


def _raw_all_row_net(raw_pbp: pl.DataFrame, dim_game: pl.DataFrame) -> pl.DataFrame:
    raw_all = (
        raw_pbp.filter(pl.col("posteam").is_not_null())
        .group_by(["game_id", "posteam"])
        .agg(pl.col("epa").sum().alias("raw_all_row_offensive_epa"))
        .rename({"posteam": "team_id"})
    )
    team_rows = pl.concat(
        [
            dim_game.select(
                "game_id",
                pl.col("home_team_id").alias("team_id"),
                pl.col("away_team_id").alias("opponent_team_id"),
            ),
            dim_game.select(
                "game_id",
                pl.col("away_team_id").alias("team_id"),
                pl.col("home_team_id").alias("opponent_team_id"),
            ),
        ],
        how="vertical",
    )
    return (
        team_rows.join(raw_all, on=["game_id", "team_id"], how="left")
        .join(
            raw_all.select(
                "game_id",
                pl.col("team_id").alias("opponent_team_id"),
                pl.col("raw_all_row_offensive_epa").alias("raw_opponent_all_row_epa"),
            ),
            on=["game_id", "opponent_team_id"],
            how="left",
        )
        .with_columns(
            (
                pl.col("raw_all_row_offensive_epa").fill_null(0.0)
                - pl.col("raw_opponent_all_row_epa").fill_null(0.0)
            ).alias("raw_all_row_net_epa")
        )
        .select(["game_id", "team_id", "raw_all_row_net_epa"])
    )


def build_epa_wpa_reconciliation(season: int) -> pl.DataFrame:
    """Build a team-game reconciliation report for EPA/WPA aggregates."""
    raw_pbp = pl.read_parquet(latest_raw_snapshot("nflverse_pbp", season))
    dim_game = pl.read_parquet(core_output_path("dim_game", season))
    fact_play = pl.read_parquet(core_output_path("fact_play", season))
    fact_team_game = pl.read_parquet(core_output_path("fact_team_game", season))

    raw_analysis = _raw_analysis_team_game(raw_pbp)
    raw_analysis_net = _raw_analysis_net(raw_analysis, dim_game)
    public_cumulative = _public_cumulative_net(raw_pbp)
    raw_all_row_net = _raw_all_row_net(raw_pbp, dim_game)
    core_wpa = (
        fact_play.filter(pl.col("posteam_id").is_not_null())
        .group_by(["game_id", "posteam_id"])
        .agg(pl.col("wpa").sum().alias("core_analysis_wpa"))
        .rename({"posteam_id": "team_id"})
    )

    report = (
        fact_team_game.select(
            "game_id",
            "team_id",
            "opponent_team_id",
            "home_away",
            "plays",
            "offensive_epa",
            "total_epa",
        )
        .join(raw_analysis, on=["game_id", "team_id"], how="left")
        .join(core_wpa, on=["game_id", "team_id"], how="left")
        .join(raw_analysis_net, on=["game_id", "team_id"], how="left")
        .join(public_cumulative, on=["game_id", "team_id"], how="left")
        .join(raw_all_row_net, on=["game_id", "team_id"], how="left")
        .with_columns(
            (pl.col("offensive_epa") - pl.col("raw_analysis_offensive_epa").fill_null(0.0)).alias(
                "offensive_epa_diff"
            ),
            (pl.col("total_epa") - pl.col("raw_analysis_net_epa").fill_null(0.0)).alias(
                "analysis_net_epa_diff"
            ),
            (
                pl.col("public_cumulative_net_epa").fill_null(0.0)
                - pl.col("raw_all_row_net_epa").fill_null(0.0)
            ).alias("public_cumulative_epa_check_diff"),
            (pl.col("core_analysis_wpa").fill_null(0.0) - pl.col("raw_analysis_wpa").fill_null(0.0))
            .alias("analysis_wpa_diff"),
            (
                pl.col("total_epa").fill_null(0.0)
                - pl.col("public_cumulative_net_epa").fill_null(0.0)
            ).alias("analysis_vs_public_cumulative_epa_gap"),
            (pl.col("plays") - pl.col("raw_analysis_plays").fill_null(0)).alias("play_count_diff"),
        )
        .sort(["game_id", "team_id"])
    )
    return report


def reconciliation_output_path(season: int) -> Path:
    """Return the local output path for the reconciliation report."""
    return (
        settings.data_dir
        / "quality"
        / "epa_wpa_reconciliation"
        / "league=nfl"
        / f"season={season}"
        / "team_game_reconciliation.parquet"
    )


def build_and_write_reconciliation(season: int) -> ReconciliationResult:
    """Write EPA/WPA reconciliation report and metadata summary."""
    report = build_epa_wpa_reconciliation(season)
    path = reconciliation_output_path(season)
    path.parent.mkdir(parents=True, exist_ok=True)
    report.write_parquet(path)
    (path.parent / "NOTICE.txt").write_text(
        attribution_block([Source.NFLVERSE]) + "\n",
        encoding="utf-8",
    )

    summary = report.select(
        pl.col("offensive_epa_diff").abs().max().alias("max_abs_offensive_epa_diff"),
        pl.col("analysis_net_epa_diff").abs().max().alias("max_abs_analysis_net_epa_diff"),
        pl.col("public_cumulative_epa_check_diff")
        .abs()
        .max()
        .alias("max_abs_public_cumulative_epa_check_diff"),
        pl.col("analysis_wpa_diff").abs().max().alias("max_abs_wpa_diff"),
        pl.col("play_count_diff").abs().max().alias("max_abs_play_count_diff"),
    ).row(0, named=True)
    result = ReconciliationResult(
        season=season,
        built_at_utc=datetime.now(UTC).isoformat(),
        report_path=str(path),
        rows=report.height,
        max_abs_offensive_epa_diff=float(summary["max_abs_offensive_epa_diff"] or 0.0),
        max_abs_analysis_net_epa_diff=float(summary["max_abs_analysis_net_epa_diff"] or 0.0),
        max_abs_public_cumulative_epa_check_diff=float(
            summary["max_abs_public_cumulative_epa_check_diff"] or 0.0
        ),
        max_abs_wpa_diff=float(summary["max_abs_wpa_diff"] or 0.0),
        max_abs_play_count_diff=int(summary["max_abs_play_count_diff"] or 0),
        notes=(
            "Core fact_team_game total_epa reconciles to analysis-play net EPA. "
            "The public cumulative nflverse total_home_epa/total_away_epa fields reconcile "
            "to all-row net EPA, including no-play/penalty bookkeeping rows; the gap column "
            "records that definitional difference."
        ),
    )
    metadata_path = settings.data_dir / "quality" / f"season={season}" / "reconciliation_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: `python -m src.quality.reconciliation --season 2025`."""
    parser = argparse.ArgumentParser(description="Build EPA/WPA reconciliation report.")
    parser.add_argument("--season", type=int, required=True)
    args = parser.parse_args(argv)
    result = build_and_write_reconciliation(args.season)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
