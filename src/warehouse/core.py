"""Build the first core NFL warehouse tables from raw nflverse snapshots."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from src.compliance.attributions import Source, attribution_block
from src.config import settings
from src.schemas.core import (
    DIM_GAME_COLUMNS,
    FACT_PLAY_COLUMNS,
    FACT_TEAM_GAME_COLUMNS,
    validate_dim_game,
    validate_fact_play,
    validate_fact_team_game,
)


@dataclass(frozen=True)
class CoreBuildResult:
    """Paths and row counts produced by a core-table build."""

    season: int
    built_at_utc: str
    dim_game_path: str
    dim_game_rows: int
    fact_play_path: str
    fact_play_rows: int
    fact_team_game_path: str
    fact_team_game_rows: int


def latest_raw_snapshot(dataset: str, season: int) -> Path:
    """Return the newest raw Parquet snapshot for a dataset/season."""
    root = settings.data_dir / "bronze" / dataset / "league=nfl" / f"season={season}"
    candidates = sorted(root.glob("pull_date=*/*.parquet"))
    if not candidates:
        raise FileNotFoundError(f"no raw {dataset} snapshot found under {root}")
    return candidates[-1]


def _weather_summary() -> pl.Expr:
    temp = pl.col("temp").cast(pl.Float64, strict=False).round(0).cast(pl.Int64, strict=False)
    wind = pl.col("wind").cast(pl.Float64, strict=False).round(0).cast(pl.Int64, strict=False)
    return (
        pl.when(pl.col("temp").is_not_null() & pl.col("wind").is_not_null())
        .then(pl.format("{}F, wind {} mph", temp, wind))
        .when(pl.col("temp").is_not_null())
        .then(pl.format("{}F", temp))
        .when(pl.col("wind").is_not_null())
        .then(pl.format("wind {} mph", wind))
        .otherwise(None)
    )


def build_dim_game(schedules: pl.DataFrame) -> pl.DataFrame:
    """Build core.dim_game from nflverse schedules."""
    dim_game = schedules.select(
        pl.col("game_id").cast(pl.Utf8),
        pl.lit("NFL").alias("league_id"),
        pl.col("season").cast(pl.Int64),
        pl.col("week").cast(pl.Int64),
        pl.col("game_type").cast(pl.Utf8).alias("season_type"),
        pl.col("home_team").cast(pl.Utf8).alias("home_team_id"),
        pl.col("away_team").cast(pl.Utf8).alias("away_team_id"),
        pl.col("gameday").cast(pl.Utf8).alias("game_date"),
        pl.col("gametime").cast(pl.Utf8).alias("kickoff_time"),
        pl.coalesce([pl.col("stadium_id").cast(pl.Utf8), pl.col("stadium").cast(pl.Utf8)]).alias(
            "venue_id"
        ),
        (pl.col("location") == "Neutral").fill_null(False).alias("neutral_site_flag"),
        pl.col("roof").cast(pl.Utf8),
        pl.col("surface").cast(pl.Utf8),
        _weather_summary().alias("weather_summary"),
        pl.col("home_score").cast(pl.Float64),
        pl.col("away_score").cast(pl.Float64),
        pl.col("spread_line").cast(pl.Float64).alias("spread_close"),
        pl.col("total_line").cast(pl.Float64).alias("total_close"),
    ).sort(["season", "week", "game_id"])
    validate_dim_game(dim_game)
    return dim_game.select(DIM_GAME_COLUMNS)


def build_fact_play(pbp: pl.DataFrame) -> pl.DataFrame:
    """Build core.fact_play from nflverse play-by-play."""
    turnover = (pl.col("interception").fill_null(0) == 1) | (pl.col("fumble_lost").fill_null(0) == 1)
    explosive = (
        ((pl.col("pass").fill_null(0) == 1) & (pl.col("yards_gained").cast(pl.Float64) >= 15))
        | ((pl.col("rush").fill_null(0) == 1) & (pl.col("yards_gained").cast(pl.Float64) >= 10))
    )
    wp_after = (
        pl.when(pl.col("posteam_type") == "home")
        .then(pl.col("home_wp_post"))
        .when(pl.col("posteam_type") == "away")
        .then(pl.col("away_wp_post"))
        .otherwise(None)
    )

    fact_play = (
        pbp.filter(pl.col("play").fill_null(0) == 1)
        .select(
            pl.col("game_id").cast(pl.Utf8),
            pl.col("play_id").cast(pl.Int64),
            pl.lit("NFL").alias("league_id"),
            pl.col("season").cast(pl.Int64),
            pl.col("week").cast(pl.Int64),
            pl.col("posteam").cast(pl.Utf8).alias("posteam_id"),
            pl.col("defteam").cast(pl.Utf8).alias("defteam_id"),
            pl.col("down").cast(pl.Float64),
            pl.col("ydstogo").cast(pl.Float64),
            pl.col("yardline_100").cast(pl.Float64),
            pl.col("half_seconds_remaining").cast(pl.Float64),
            pl.col("game_seconds_remaining").cast(pl.Float64),
            pl.col("score_differential").cast(pl.Float64),
            pl.col("play_type").cast(pl.Utf8),
            (pl.col("pass").fill_null(0) == 1).alias("pass_flag"),
            (pl.col("rush").fill_null(0) == 1).alias("rush_flag"),
            (pl.col("special_teams_play").fill_null(0) == 1).alias("special_teams_flag"),
            pl.col("passer_player_id").cast(pl.Utf8),
            pl.col("rusher_player_id").cast(pl.Utf8),
            pl.col("receiver_player_id").cast(pl.Utf8),
            pl.col("epa").cast(pl.Float64),
            pl.col("wp").cast(pl.Float64).alias("wp_before"),
            wp_after.cast(pl.Float64).alias("wp_after"),
            pl.col("wpa").cast(pl.Float64),
            (pl.col("success").fill_null(0) == 1).alias("success_flag"),
            pl.col("yards_gained").cast(pl.Float64),
            (pl.col("touchdown").fill_null(0) == 1).alias("touchdown_flag"),
            turnover.alias("turnover_flag"),
            (pl.col("penalty").fill_null(0) == 1).alias("penalty_flag"),
            explosive.fill_null(False).alias("explosive_flag"),
            pl.col("pass_oe").cast(pl.Float64).alias("pass_rate_over_expected"),
        )
        .sort(["game_id", "play_id"])
    )
    validate_fact_play(fact_play)
    return fact_play.select(FACT_PLAY_COLUMNS)


def _team_rows(dim_game: pl.DataFrame) -> pl.DataFrame:
    home = dim_game.select(
        "game_id",
        pl.col("home_team_id").alias("team_id"),
        pl.col("away_team_id").alias("opponent_team_id"),
        pl.lit("home").alias("home_away"),
        pl.col("home_score").alias("points_for"),
        pl.col("away_score").alias("points_against"),
    )
    away = dim_game.select(
        "game_id",
        pl.col("away_team_id").alias("team_id"),
        pl.col("home_team_id").alias("opponent_team_id"),
        pl.lit("away").alias("home_away"),
        pl.col("away_score").alias("points_for"),
        pl.col("home_score").alias("points_against"),
    )
    return pl.concat([home, away], how="vertical")


def _mean_bool(column: str) -> pl.Expr:
    return pl.col(column).cast(pl.Float64).mean()


def build_fact_team_game(dim_game: pl.DataFrame, fact_play: pl.DataFrame) -> pl.DataFrame:
    """Build one team-game row per team from dim_game and fact_play."""
    non_special = pl.col("special_teams_flag") == False  # noqa: E712
    offense = (
        fact_play.filter(pl.col("posteam_id").is_not_null())
        .group_by(["game_id", "posteam_id"])
        .agg(
            pl.len().alias("plays"),
            pl.col("epa").filter(non_special).sum().alias("offensive_epa"),
            pl.col("epa").filter(pl.col("special_teams_flag")).sum().alias("special_teams_epa"),
            pl.col("success_flag").filter(non_special).cast(pl.Float64).mean().alias("success_rate"),
            pl.col("explosive_flag").filter(non_special).cast(pl.Float64).mean().alias("explosive_rate"),
            pl.col("turnover_flag").cast(pl.Int64).sum().alias("turnovers_committed"),
            pl.col("pass_rate_over_expected").mean().alias("pass_rate_over_expected"),
        )
        .rename({"posteam_id": "team_id"})
    )
    defense = (
        fact_play.filter(pl.col("defteam_id").is_not_null())
        .group_by(["game_id", "defteam_id"])
        .agg(
            pl.col("epa").filter(non_special).sum().alias("defensive_epa_allowed"),
            pl.col("turnover_flag").cast(pl.Int64).sum().alias("turnovers_forced"),
        )
        .rename({"defteam_id": "team_id"})
    )

    fact_team_game = (
        _team_rows(dim_game)
        .join(offense, on=["game_id", "team_id"], how="left")
        .join(defense, on=["game_id", "team_id"], how="left")
        .with_columns(
            pl.col("plays").fill_null(0).cast(pl.Int64),
            pl.col("offensive_epa").fill_null(0.0),
            pl.col("special_teams_epa").fill_null(0.0),
            pl.col("defensive_epa_allowed").fill_null(0.0),
            pl.col("turnovers_committed").fill_null(0).cast(pl.Int64),
            pl.col("turnovers_forced").fill_null(0).cast(pl.Int64),
            pl.col("success_rate").cast(pl.Float64),
            pl.col("explosive_rate").cast(pl.Float64),
            pl.col("pass_rate_over_expected").cast(pl.Float64),
            (pl.col("points_for") > pl.col("points_against")).fill_null(False).alias("win_flag"),
        )
        .with_columns(
            (
                pl.col("offensive_epa")
                + pl.col("special_teams_epa")
                - pl.col("defensive_epa_allowed")
            ).alias("total_epa"),
            (pl.col("turnovers_forced") - pl.col("turnovers_committed"))
            .cast(pl.Float64)
            .alias("turnover_margin"),
            pl.lit(None).cast(pl.Float64).alias("pace_seconds_per_play"),
            pl.lit(None).cast(pl.Float64).alias("fourth_down_aggressiveness"),
        )
        .select(FACT_TEAM_GAME_COLUMNS)
        .sort(["game_id", "team_id"])
    )
    validate_fact_team_game(fact_team_game)
    return fact_team_game


def core_output_path(table: str, season: int) -> Path:
    """Return the local output path for a core table/season."""
    return settings.data_dir / "core" / table / "league=nfl" / f"season={season}" / f"{table}.parquet"


def _write_core_table(frame: pl.DataFrame, table: str, season: int) -> Path:
    path = core_output_path(table, season)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)
    (path.parent / "NOTICE.txt").write_text(
        attribution_block([Source.NFLVERSE]) + "\n",
        encoding="utf-8",
    )
    return path


def build_core_tables(season: int) -> CoreBuildResult:
    """Read raw snapshots, build validated core tables, and write them to data/core."""
    schedules = pl.read_parquet(latest_raw_snapshot("nflverse_schedules", season))
    pbp = pl.read_parquet(latest_raw_snapshot("nflverse_pbp", season))

    dim_game = build_dim_game(schedules)
    fact_play = build_fact_play(pbp)
    fact_team_game = build_fact_team_game(dim_game, fact_play)

    dim_game_path = _write_core_table(dim_game, "dim_game", season)
    fact_play_path = _write_core_table(fact_play, "fact_play", season)
    fact_team_game_path = _write_core_table(fact_team_game, "fact_team_game", season)

    result = CoreBuildResult(
        season=season,
        built_at_utc=datetime.now(UTC).isoformat(),
        dim_game_path=str(dim_game_path),
        dim_game_rows=dim_game.height,
        fact_play_path=str(fact_play_path),
        fact_play_rows=fact_play.height,
        fact_team_game_path=str(fact_team_game_path),
        fact_team_game_rows=fact_team_game.height,
    )
    metadata_path = settings.data_dir / "core" / f"season={season}" / "core_build_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    return result


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint: `python -m src.warehouse.core --season 2025`."""
    parser = argparse.ArgumentParser(description="Build core warehouse tables from raw snapshots.")
    parser.add_argument("--season", type=int, required=True)
    args = parser.parse_args(argv)
    result = build_core_tables(args.season)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
