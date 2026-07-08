"""Bronze/raw-layer validation for football source extracts."""

from __future__ import annotations

from typing import Any

NFL_PBP_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "game_id",
        "season",
        "week",
        "posteam",
        "defteam",
        "play_id",
        "down",
        "ydstogo",
        "yardline_100",
        "epa",
        "wpa",
    }
)

NFL_SCHEDULE_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "game_type",
    }
)


def columns_of(frame: Any) -> set[str]:
    """Return dataframe columns for pandas/polars-like objects."""
    if hasattr(frame, "columns"):
        return set(frame.columns)
    raise TypeError("frame must expose a columns attribute")


def validate_required_columns(frame: Any, required: frozenset[str], *, table: str) -> None:
    """Raise a clear error if a raw extract is missing required columns."""
    missing = sorted(required - columns_of(frame))
    if missing:
        raise ValueError(f"{table} missing required columns: {', '.join(missing)}")


def validate_nfl_pbp_columns(frame: Any) -> None:
    """Validate required nflverse play-by-play columns."""
    validate_required_columns(frame, NFL_PBP_REQUIRED_COLUMNS, table="nflverse_pbp")


def validate_nfl_schedule_columns(frame: Any) -> None:
    """Validate required nflverse schedule columns."""
    validate_required_columns(frame, NFL_SCHEDULE_REQUIRED_COLUMNS, table="nflverse_schedules")
