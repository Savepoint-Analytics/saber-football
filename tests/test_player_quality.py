"""Regression checks for player-context sources and coverage denominators."""

import polars as pl

from src.quality.player_context import audit_snap_ids, team_game_coverage


def test_snap_id_audit_keeps_conflicting_roster_id_unresolved():
    raw = pl.DataFrame(
        {
            "pfr_player_id": ["match", "unmapped", "missing"],
            "player": ["Player One", "Player Two", "Player Three"],
            "team": ["AAA", "AAA", "BBB"],
            "position": ["WR"] * 3,
            "game_id": ["g1"] * 3,
        }
    )
    bridge = pl.DataFrame({"pfr_id": ["match"], "player_id": ["gsis1"]})
    rosters = pl.DataFrame(
        {"full_name": ["Player Two"], "team": ["AAA"], "gsis_id": ["gsis2"], "pfr_id": ["old"]}
    )
    snaps, review = audit_snap_ids(raw, bridge, rosters)
    assert snaps["bridge_matches"].to_list() == [1, 0, 0]
    assert dict(review.select("pfr_id", "review_status").iter_rows()) == {
        "unmapped": "conflicting_roster_pfr_id",
        "missing": "no_same_team_roster_candidate",
    }


def test_team_coverage_counts_missing_team_and_excludes_non_analysis_plays():
    games = pl.DataFrame(
        {"game_id": ["g1"], "week": [1], "home_team_id": ["AAA"], "away_team_id": ["BBB"]}
    )
    plays = pl.DataFrame(
        {"game_id": ["g1"], "play_id": [1], "posteam_id": ["AAA"], "defteam_id": ["BBB"]}
    )
    snaps = pl.DataFrame({"game_id": ["g1"], "team_id": ["AAA"], "bridge_matches": [1]})
    participation = pl.DataFrame(
        {
            "game_id": ["g1", "g1"],
            "play_id": [1, 3],
            "team_id": ["AAA", "BBB"],
            "side": ["offense", "defense"],
            "player_id": ["a", "b"],
        }
    )
    coverage = team_game_coverage(games, plays, snaps, snaps, participation)
    assert coverage["analysis_play_sides"].to_list() == [1, 1]
    assert coverage["participation_coverage_rate"].to_list() == [1.0, 0.0]
    assert coverage["eleven_player_sides"].to_list() == [0, 0]
    assert coverage["snap_id_match_rate"].to_list() == [1.0, None]
