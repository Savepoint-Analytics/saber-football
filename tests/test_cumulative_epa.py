"""Highest-ID administrative events must be identified separately from END GAME."""

import polars as pl

from src.quality.reconciliation import trace_cumulative_epa


def test_trace_localizes_gap_to_administrative_row_after_end_game():
    raw = pl.DataFrame(
        {
            "game_id": ["g1", "g1", "g1"],
            "play_id": [3, 1, 2],
            "total_home_epa": [4.0, 1.0, 1.0],
            "epa": [0.0, 1.0, None],
            "timeout": [1, 0, None],
            "desc": ["Timeout", "Run", "END GAME"],
            "play_type": ["no_play", "run", None],
        }
    )
    report = pl.DataFrame(
        {
            "game_id": ["g1", "g1"],
            "home_away": ["home", "away"],
            "raw_all_row_net_epa": [1.0, -1.0],
            "public_cumulative_epa_check_diff": [3.0, -3.0],
        }
    )
    result = trace_cumulative_epa(raw, report).row(0, named=True)
    assert result["highest_id_event"] == "timeout"
    assert result["highest_id_after_end_game"]
    assert result["end_game_epa_gap"] == 0
