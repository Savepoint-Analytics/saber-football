"""Player opportunity denominators and missing coverage."""

import polars as pl

from src.analytics.player_opportunity import build_opportunity, exact_snap_total
from src.warehouse.identity import build_fact_player_game


def test_snap_total_requires_one_denominator_compatible_with_source_percentages():
    assert exact_snap_total([(63, 1.0), (32, 0.51), (0, 0.0)]) == 63
    assert exact_snap_total([(50, 0.50)]) is None
    assert exact_snap_total([(60, 1.0), (61, 0.99)]) is None


def test_season_share_uses_only_games_with_confirmed_denominators():
    games = pl.DataFrame(
        {
            "game_id": ["g1", "g2", "g3"],
            "season": [2025] * 3,
            "week": [1, 2, 3],
            "season_type": ["REG"] * 3,
            "home_team_id": ["AAA"] * 3,
            "away_team_id": ["BBB"] * 3,
            "home_score": [20] * 3,
            "away_score": [10] * 3,
        }
    )
    plays = pl.DataFrame(
        {
            "game_id": ["g1", "g1", "g2"],
            "play_id": [1, 2, 1],
            "posteam_id": ["AAA"] * 3,
            "defteam_id": ["BBB"] * 3,
        }
    )
    players = pl.DataFrame(
        {
            "player_id": ["p1", "p2"],
            "full_name": ["Player One", "Player Two"],
            "primary_position": ["QB", "WR"],
        }
    )
    bridge = pl.DataFrame({"player_id": ["p1", "p2"], "pfr_id": ["id1", "id2"]})
    snaps = pl.DataFrame(
        {
            "game_id": ["g1", "g1", "g2"],
            "team": ["AAA"] * 3,
            "pfr_player_id": ["id1", "id2", "id1"],
            "player": ["Player One", "Player Two", "Player One"],
            "position": ["QB", "WR", "QB"],
            "offense_snaps": [32.0, 63.0, 50.0],
            "offense_pct": [0.51, 1.0, 0.50],
            "defense_snaps": [0.0] * 3,
            "defense_pct": [0.0] * 3,
            "st_snaps": [0.0] * 3,
            "st_pct": [0.0] * 3,
        }
    )
    participation = pl.DataFrame(
        {
            "game_id": ["g1"],
            "play_id": [1],
            "team_id": ["AAA"],
            "side": ["offense"],
            "player_id": ["p1"],
        }
    )
    by_game, by_season = build_opportunity(
        games, plays, players, bridge, build_fact_player_game(snaps, bridge), participation, snaps
    )
    player = by_season.filter(pl.col("player_id") == "p1").row(0, named=True)
    assert player["snaps_offense"] == 82
    assert player["offense_share_snaps"] == 32
    assert player["offense_team_snaps"] == 63
    assert player["offense_snap_share"] == 32 / 63
    assert player["offense_share_games"] == 1
    assert player["offense_snap_source_games"] == 2
    assert player["team_games"] == 3
    assert player["offense_on_field"] == 1
    assert player["offense_expected_plays"] == 3
    assert player["offense_covered_plays"] == 1
    assert (
        by_game.filter(pl.col("game_id") == "g2")["offense_share_basis"].item()
        == "PFR rounded share"
    )
    assert by_game.filter(pl.col("game_id") == "g2")["offense_on_field"].item() is None
