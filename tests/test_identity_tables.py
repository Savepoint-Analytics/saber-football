"""Identity and player-context warehouse transform tests."""

import polars as pl
import pytest

from src.warehouse.identity import (
    build_bridge_player_ids,
    build_dim_player,
    build_dim_team,
    build_fact_player_game,
    build_fact_player_on_play,
)


def test_dim_team_and_player_bridge_build_from_source_ids():
    teams = pl.DataFrame(
        {
            "team_abbr": ["AAA"],
            "team_name": ["Alpha Aardvarks"],
            "team_id": ["0001"],
            "team_conf": ["AFC"],
            "team_division": ["AFC Test"],
        }
    )
    players = pl.DataFrame(
        {
            "gsis_id": ["00-0000001"],
            "display_name": ["Test Player"],
            "birth_date": ["2000-01-01"],
            "height": [72],
            "weight": [220],
            "position": ["QB"],
            "college_name": ["Example"],
            "pfr_id": ["PlayTe00"],
            "pff_id": ["123"],
            "otc_id": [None],
            "espn_id": ["999"],
            "esb_id": [None],
            "nfl_id": [None],
            "smart_id": ["smart"],
        }
    )

    dim_team = build_dim_team(teams)
    dim_player = build_dim_player(players)
    bridge = build_bridge_player_ids(players)

    assert dim_team.select("team_id").item() == "AAA"
    assert dim_player.select("player_id").item() == "00-0000001"
    assert bridge.select("pfr_id").item() == "PlayTe00"


def test_fact_player_game_uses_gsis_when_pfr_bridge_exists():
    snap_counts = pl.DataFrame(
        {
            "game_id": ["g1"],
            "pfr_player_id": ["PlayTe00"],
            "player": ["Test Player"],
            "team": ["AAA"],
            "position": ["QB"],
            "offense_snaps": [60.0],
            "defense_snaps": [0.0],
            "st_snaps": [0.0],
        }
    )
    bridge = pl.DataFrame({"player_id": ["00-0000001"], "pfr_id": ["PlayTe00"]})

    fact = build_fact_player_game(snap_counts, bridge)

    row = fact.row(0, named=True)
    assert row["player_id"] == "00-0000001"
    assert row["active_flag"] is True
    assert row["snaps_offense"] == 60.0


@pytest.mark.parametrize(
    ("player_ids", "player_names", "positions", "expected_position"),
    [
        ("00-0000002", "Defense Player", "LB", "LB"),
        ("00-0000002;00-0000002", "Defense Player;Defense Player", "DE;LB", None),
    ],
)
def test_fact_player_on_play_uses_dim_game_fallback_for_non_analysis_play(
    player_ids, player_names, positions, expected_position
):
    participation = pl.DataFrame(
        {
            "nflverse_game_id": ["g1"],
            "play_id": [40.0],
            "possession_team": ["AAA"],
            "offense_players": ["00-0000001"],
            "defense_players": [player_ids],
            "offense_names": ["Offense Player"],
            "defense_names": [player_names],
            "offense_positions": ["QB"],
            "defense_positions": [positions],
            "offense_personnel": ["11"],
            "defense_personnel": ["nickel"],
            "defenders_in_box": [6],
            "number_of_pass_rushers": [4],
        }
    )
    fact_play = pl.DataFrame(
        {
            "game_id": ["g1"],
            "play_id": [99],
            "posteam_id": ["AAA"],
            "defteam_id": ["BBB"],
        }
    )
    dim_game = pl.DataFrame(
        {
            "game_id": ["g1"],
            "home_team_id": ["BBB"],
            "away_team_id": ["AAA"],
        }
    )

    fact = build_fact_player_on_play(participation, fact_play, dim_game)

    assert fact.height == 2
    assert fact.filter(pl.col("side") == "offense").select("team_id").item() == "AAA"
    defense = fact.filter(pl.col("side") == "defense")
    assert defense.select("team_id").item() == "BBB"
    assert defense.select("position").item() == expected_position
