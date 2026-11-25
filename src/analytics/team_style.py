"""Build team efficiency/style marts from core football tables."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, attribution_block
from src.config import settings
from src.warehouse.core import core_metadata_path, core_output_path
from src.warehouse.snapshots import Snapshot, read_build_inputs

TEAM_STYLE_SEASON_COLUMNS: tuple[str, ...] = (
    "season",
    "team_id",
    "games",
    "wins",
    "points_for_per_game",
    "points_against_per_game",
    "point_diff_per_game",
    "total_epa_per_game",
    "offensive_epa_per_play",
    "defensive_epa_allowed_per_game",
    "special_teams_epa_per_game",
    "success_rate",
    "explosive_rate",
    "pass_rate_over_expected",
    "turnover_margin_per_game",
    "plays_per_game",
)


@dataclass(frozen=True)
class TeamStyleBuildResult:
    """Paths and row counts produced by the team-style build."""

    season: int
    built_at_utc: str
    team_style_season_path: str
    team_style_season_rows: int
    raw_inputs: dict[str, Snapshot]


def _weighted_mean(metric: str, weight: str = "plays") -> pl.Expr:
    valid = pl.col(metric).is_not_null() & pl.col(weight).is_not_null() & (pl.col(weight) > 0)
    numerator = (pl.col(metric) * pl.col(weight)).filter(valid).sum()
    denominator = pl.col(weight).filter(valid).sum()
    return (numerator / denominator).alias(metric)


def build_team_style_season(fact_team_game: pl.DataFrame, *, season: int) -> pl.DataFrame:
    """Build one season-level team efficiency/style row per team."""
    style = (
        fact_team_game.group_by("team_id")
        .agg(
            pl.lit(season).alias("season"),
            pl.len().alias("games"),
            pl.col("win_flag").cast(pl.Int64).sum().alias("wins"),
            pl.col("points_for").mean().alias("points_for_per_game"),
            pl.col("points_against").mean().alias("points_against_per_game"),
            (pl.col("points_for") - pl.col("points_against")).mean().alias("point_diff_per_game"),
            pl.col("total_epa").mean().alias("total_epa_per_game"),
            (pl.col("offensive_epa").sum() / pl.col("plays").sum()).alias("offensive_epa_per_play"),
            pl.col("defensive_epa_allowed").mean().alias("defensive_epa_allowed_per_game"),
            pl.col("special_teams_epa").mean().alias("special_teams_epa_per_game"),
            _weighted_mean("success_rate"),
            _weighted_mean("explosive_rate"),
            _weighted_mean("pass_rate_over_expected"),
            pl.col("turnover_margin").mean().alias("turnover_margin_per_game"),
            pl.col("plays").mean().alias("plays_per_game"),
        )
        .select(TEAM_STYLE_SEASON_COLUMNS)
        .sort("team_id")
    )
    return style


def team_style_output_path(season: int) -> Path:
    """Return the local output path for analytics.team_style_season."""
    return (
        settings.data_dir
        / "analytics"
        / "team_style_season"
        / "league=nfl"
        / f"season={season}"
        / "team_style_season.parquet"
    )


def build_and_write_team_style(season: int) -> TeamStyleBuildResult:
    """Read core fact_team_game, build the team-style mart, and write it."""
    fact_team_game = pl.read_parquet(core_output_path("fact_team_game", season))
    team_style = build_team_style_season(fact_team_game, season=season)
    path = team_style_output_path(season)
    path.parent.mkdir(parents=True, exist_ok=True)
    team_style.write_parquet(path)
    (path.parent / "NOTICE.txt").write_text(
        attribution_block([Source.NFLVERSE]) + "\n",
        encoding="utf-8",
    )
    result = TeamStyleBuildResult(
        season=season,
        built_at_utc=datetime.now(UTC).isoformat(),
        team_style_season_path=str(path),
        team_style_season_rows=team_style.height,
        raw_inputs=read_build_inputs(core_metadata_path(season), season) or {},
    )
    metadata_path = (
        settings.data_dir / "analytics" / f"season={season}" / "team_style_metadata.json"
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: `python -m src.analytics.team_style --season 2025`."""
    parser = argparse.ArgumentParser(description="Build team style analytics mart.")
    parser.add_argument("--season", type=int, required=True)
    args = parser.parse_args(argv)
    result = build_and_write_team_style(args.season)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
