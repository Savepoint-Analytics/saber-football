"""Pandera validation for first-pass core warehouse tables."""

from __future__ import annotations

from typing import Any

import pandera.pandas as pa
from pandera import Check, Column

DIM_GAME_COLUMNS: tuple[str, ...] = (
    "game_id",
    "league_id",
    "season",
    "week",
    "season_type",
    "home_team_id",
    "away_team_id",
    "game_date",
    "kickoff_time",
    "venue_id",
    "neutral_site_flag",
    "roof",
    "surface",
    "weather_summary",
    "home_score",
    "away_score",
    "spread_close",
    "total_close",
)

FACT_PLAY_COLUMNS: tuple[str, ...] = (
    "game_id",
    "play_id",
    "league_id",
    "season",
    "week",
    "posteam_id",
    "defteam_id",
    "down",
    "ydstogo",
    "yardline_100",
    "half_seconds_remaining",
    "game_seconds_remaining",
    "score_differential",
    "play_type",
    "pass_flag",
    "rush_flag",
    "special_teams_flag",
    "passer_player_id",
    "rusher_player_id",
    "receiver_player_id",
    "epa",
    "wp_before",
    "wp_after",
    "wpa",
    "success_flag",
    "yards_gained",
    "touchdown_flag",
    "turnover_flag",
    "penalty_flag",
    "explosive_flag",
    "pass_rate_over_expected",
)

FACT_TEAM_GAME_COLUMNS: tuple[str, ...] = (
    "game_id",
    "team_id",
    "opponent_team_id",
    "home_away",
    "points_for",
    "points_against",
    "win_flag",
    "total_epa",
    "offensive_epa",
    "defensive_epa_allowed",
    "special_teams_epa",
    "success_rate",
    "explosive_rate",
    "turnover_margin",
    "plays",
    "pace_seconds_per_play",
    "pass_rate_over_expected",
    "fourth_down_aggressiveness",
)


DIM_GAME_SCHEMA = pa.DataFrameSchema(
    {
        "game_id": Column(str, nullable=False, unique=True),
        "league_id": Column(str, nullable=False, checks=Check.isin(["NFL"])),
        "season": Column(int, nullable=False),
        "week": Column(int, nullable=False),
        "season_type": Column(str, nullable=False),
        "home_team_id": Column(str, nullable=False),
        "away_team_id": Column(str, nullable=False),
        "game_date": Column(str, nullable=True),
        "kickoff_time": Column(str, nullable=True),
        "venue_id": Column(str, nullable=True),
        "neutral_site_flag": Column(bool, nullable=False),
        "roof": Column(str, nullable=True),
        "surface": Column(str, nullable=True),
        "weather_summary": Column(str, nullable=True),
        "home_score": Column(float, nullable=True),
        "away_score": Column(float, nullable=True),
        "spread_close": Column(float, nullable=True),
        "total_close": Column(float, nullable=True),
    },
    strict=True,
)

FACT_PLAY_SCHEMA = pa.DataFrameSchema(
    {
        "game_id": Column(str, nullable=False),
        "play_id": Column(int, nullable=False),
        "league_id": Column(str, nullable=False, checks=Check.isin(["NFL"])),
        "season": Column(int, nullable=False),
        "week": Column(int, nullable=False),
        "posteam_id": Column(str, nullable=True),
        "defteam_id": Column(str, nullable=True),
        "down": Column(float, nullable=True),
        "ydstogo": Column(float, nullable=True),
        "yardline_100": Column(float, nullable=True),
        "half_seconds_remaining": Column(float, nullable=True),
        "game_seconds_remaining": Column(float, nullable=True),
        "score_differential": Column(float, nullable=True),
        "play_type": Column(str, nullable=True),
        "pass_flag": Column(bool, nullable=False),
        "rush_flag": Column(bool, nullable=False),
        "special_teams_flag": Column(bool, nullable=False),
        "passer_player_id": Column(str, nullable=True),
        "rusher_player_id": Column(str, nullable=True),
        "receiver_player_id": Column(str, nullable=True),
        "epa": Column(float, nullable=True),
        "wp_before": Column(float, nullable=True),
        "wp_after": Column(float, nullable=True),
        "wpa": Column(float, nullable=True),
        "success_flag": Column(bool, nullable=False),
        "yards_gained": Column(float, nullable=True),
        "touchdown_flag": Column(bool, nullable=False),
        "turnover_flag": Column(bool, nullable=False),
        "penalty_flag": Column(bool, nullable=False),
        "explosive_flag": Column(bool, nullable=False),
        "pass_rate_over_expected": Column(float, nullable=True),
    },
    strict=True,
)

FACT_TEAM_GAME_SCHEMA = pa.DataFrameSchema(
    {
        "game_id": Column(str, nullable=False),
        "team_id": Column(str, nullable=False),
        "opponent_team_id": Column(str, nullable=False),
        "home_away": Column(str, nullable=False, checks=Check.isin(["home", "away"])),
        "points_for": Column(float, nullable=True),
        "points_against": Column(float, nullable=True),
        "win_flag": Column(bool, nullable=False),
        "total_epa": Column(float, nullable=True),
        "offensive_epa": Column(float, nullable=True),
        "defensive_epa_allowed": Column(float, nullable=True),
        "special_teams_epa": Column(float, nullable=True),
        "success_rate": Column(float, nullable=True),
        "explosive_rate": Column(float, nullable=True),
        "turnover_margin": Column(float, nullable=True),
        "plays": Column(int, nullable=False),
        "pace_seconds_per_play": Column(float, nullable=True),
        "pass_rate_over_expected": Column(float, nullable=True),
        "fourth_down_aggressiveness": Column(float, nullable=True),
    },
    strict=True,
)


def validate_dim_game(frame: Any) -> None:
    """Validate dim_game using Pandera."""
    DIM_GAME_SCHEMA.validate(frame.to_pandas())


def validate_fact_play(frame: Any) -> None:
    """Validate fact_play using Pandera."""
    FACT_PLAY_SCHEMA.validate(frame.to_pandas())


def validate_fact_team_game(frame: Any) -> None:
    """Validate fact_team_game using Pandera."""
    FACT_TEAM_GAME_SCHEMA.validate(frame.to_pandas())
