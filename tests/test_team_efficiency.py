"""Efficiency validation uses only games before each evaluated week."""

import polars as pl
from polars.testing import assert_frame_equal

from src.analytics import team_efficiency


def test_week_five_prediction_does_not_use_week_five_outcomes(monkeypatch):
    monkeypatch.setattr(team_efficiency, "BOOTSTRAP_DRAWS", 5)
    rows = pl.DataFrame(
        {
            "season": [2025] * 8,
            "season_type": ["REG"] * 8,
            "week": [1, 1, 2, 2, 5, 5, 6, 6],
            "game_id": ["g1", "g1", "g2", "g2", "g5", "g5", "g6", "g6"],
            "team_id": ["AAA", "BBB"] * 4,
            "opponent_team_id": ["BBB", "AAA"] * 4,
            "venue": [0.0] * 8,
            "plays": [50] * 8,
            "epa_per_play": [0.2, 0.0, 0.3, -0.1, 0.1, -0.2, 0.3, -0.3],
        }
    ).with_columns(epa=pl.col("epa_per_play") * pl.col("plays"))
    ratings, original = team_efficiency.adjusted_efficiency(rows)
    _, changed = team_efficiency.adjusted_efficiency(
        rows.with_columns(
            pl.when(pl.col("week") == 5)
            .then(pl.col("epa_per_play") + 1)
            .otherwise(pl.col("epa_per_play"))
            .alias("epa_per_play")
        )
    )
    columns = ["offense_only", "opponent_adjusted"]
    assert_frame_equal(
        original.filter(pl.col("week") == 5).select(columns),
        changed.filter(pl.col("week") == 5).select(columns),
    )
    assert ratings["games"].to_list() == [4, 4]
    assert ratings["net_adjusted_epa"][0] > 0
    assert ratings["team_id"][0] == "AAA"
