"""Team style analytics mart tests."""

import polars as pl

from src.analytics.team_style import build_team_style_season


def test_team_style_season_builds_one_row_per_team():
    fact_team_game = pl.DataFrame(
        {
            "game_id": ["g1", "g1", "g2"],
            "team_id": ["AAA", "BBB", "AAA"],
            "opponent_team_id": ["BBB", "AAA", "CCC"],
            "home_away": ["home", "away", "away"],
            "points_for": [24.0, 17.0, 20.0],
            "points_against": [17.0, 24.0, 23.0],
            "win_flag": [True, False, False],
            "total_epa": [4.0, -4.0, -2.0],
            "offensive_epa": [6.0, -2.0, 2.0],
            "defensive_epa_allowed": [2.0, 6.0, 4.0],
            "special_teams_epa": [0.0, -1.0, 0.0],
            "success_rate": [0.5, 0.4, 0.25],
            "explosive_rate": [0.2, 0.1, 0.05],
            "turnover_margin": [1.0, -1.0, -2.0],
            "plays": [60, 58, 40],
            "pace_seconds_per_play": [None, None, None],
            "pass_rate_over_expected": [3.0, -2.0, 1.0],
            "fourth_down_aggressiveness": [None, None, None],
        }
    )

    style = build_team_style_season(fact_team_game, season=2025)
    aaa = style.filter(pl.col("team_id") == "AAA").row(0, named=True)

    assert style.height == 2
    assert aaa["games"] == 2
    assert aaa["wins"] == 1
    assert round(aaa["offensive_epa_per_play"], 4) == 0.08
    assert round(aaa["success_rate"], 4) == 0.4
