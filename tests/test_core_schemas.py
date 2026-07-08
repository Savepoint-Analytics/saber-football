"""Core warehouse transforms and Pandera validation."""

import polars as pl
import pytest

from src.schemas.core import validate_fact_play
from src.warehouse.core import build_dim_game, build_fact_play, build_fact_team_game


def schedule_fixture() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": ["2025_01_AAA_BBB"],
            "season": [2025],
            "game_type": ["REG"],
            "week": [1],
            "gameday": ["2025-09-07"],
            "gametime": ["13:00"],
            "away_team": ["AAA"],
            "away_score": [17],
            "home_team": ["BBB"],
            "home_score": [24],
            "location": ["Home"],
            "spread_line": [-3.5],
            "total_line": [44.5],
            "roof": ["outdoors"],
            "surface": ["grass"],
            "temp": [72],
            "wind": [8],
            "stadium_id": ["BBB00"],
            "stadium": ["Example Field"],
        }
    )


def pbp_fixture() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": ["2025_01_AAA_BBB", "2025_01_AAA_BBB", "2025_01_AAA_BBB"],
            "play_id": [1.0, 40.0, 65.0],
            "season": [2025, 2025, 2025],
            "week": [1, 1, 1],
            "posteam": [None, "AAA", "BBB"],
            "posteam_type": [None, "away", "home"],
            "defteam": [None, "BBB", "AAA"],
            "down": [None, 1.0, 1.0],
            "ydstogo": [0.0, 10.0, 10.0],
            "yardline_100": [None, 75.0, 60.0],
            "half_seconds_remaining": [1800.0, 1790.0, 1710.0],
            "game_seconds_remaining": [3600.0, 3590.0, 3510.0],
            "score_differential": [None, 0.0, 0.0],
            "play_type": [None, "pass", "run"],
            "pass": [0.0, 1.0, 0.0],
            "rush": [0.0, 0.0, 1.0],
            "special_teams_play": [0.0, 0.0, 0.0],
            "passer_player_id": [None, "00-0000001", None],
            "rusher_player_id": [None, None, "00-0000002"],
            "receiver_player_id": [None, "00-0000003", None],
            "epa": [0.0, 1.2, -0.4],
            "wp": [0.5, 0.45, 0.55],
            "home_wp_post": [0.5, 0.43, 0.52],
            "away_wp_post": [0.5, 0.57, 0.48],
            "wpa": [0.0, 0.12, -0.03],
            "success": [0.0, 1.0, 0.0],
            "yards_gained": [0.0, 18.0, 4.0],
            "touchdown": [0.0, 0.0, 0.0],
            "interception": [0.0, 0.0, 0.0],
            "fumble_lost": [0.0, 0.0, 1.0],
            "penalty": [None, 0.0, 0.0],
            "pass_oe": [None, 12.0, -8.0],
            "play": [0.0, 1.0, 1.0],
        }
    )


def test_core_transforms_build_expected_grains():
    dim_game = build_dim_game(schedule_fixture())
    fact_play = build_fact_play(pbp_fixture())
    fact_team_game = build_fact_team_game(dim_game, fact_play)

    assert dim_game.shape == (1, 18)
    assert fact_play.shape == (2, 31)
    assert fact_team_game.shape == (2, 18)
    assert fact_play["explosive_flag"].to_list() == [True, False]
    assert fact_team_game.filter(pl.col("team_id") == "AAA")["turnover_margin"].item() == 1.0


def test_fact_play_schema_rejects_missing_required_column():
    fact_play = build_fact_play(pbp_fixture()).drop("epa")
    with pytest.raises(Exception, match="epa"):
        validate_fact_play(fact_play)
