"""Raw extract schema guardrails."""

import pytest

from src.schemas.bronze import (
    NFL_PBP_REQUIRED_COLUMNS,
    validate_nfl_pbp_columns,
    validate_nfl_schedule_columns,
)


class Frame:
    def __init__(self, columns):
        self.columns = columns


def test_pbp_required_columns_accepts_minimal_frame():
    validate_nfl_pbp_columns(Frame(columns=list(NFL_PBP_REQUIRED_COLUMNS)))


def test_pbp_required_columns_reports_missing():
    with pytest.raises(ValueError, match="epa"):
        validate_nfl_pbp_columns(Frame(columns=["game_id", "season"]))


def test_schedule_required_columns_accepts_minimal_frame():
    validate_nfl_schedule_columns(
        Frame(columns=["game_id", "season", "week", "home_team", "away_team", "game_type"])
    )
