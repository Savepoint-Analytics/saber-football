"""Streamlit views for player opportunity and source coverage."""

from __future__ import annotations

import polars as pl
import streamlit as st

from src.analytics.player_opportunity import PHASES, SIDES, opportunity_path
from src.compliance.attributions import Source, attribution_block, participation_source

SNAP_NOTE = (
    "Snap shares use PFR team snaps for the player's recorded games. Season shares include "
    "only games with a uniquely reconstructed team denominator. Game shares can fall back "
    "to the rounded PFR value."
)
ON_FIELD_NOTE = (
    "Covered plays have a recorded lineup. Eligible plays are all analysis plays on that "
    "team side during the player's listed games. Counts reflect recorded appearances."
)
PHASE_LABELS = {"offense": "Offense", "defense": "Defense", "special_teams": "Special teams"}


def _snap_columns(phase: str, season_view: bool) -> dict[str, str]:
    columns = {f"snaps_{phase}": "Player snaps", f"{phase}_team_snaps": "Team snaps in share"}
    if season_view:
        columns.update(
            {
                f"{phase}_share_snaps": "Player snaps in share",
                f"{phase}_share_games": "Games in share",
                f"{phase}_snap_source_games": "Games with snap counts",
            }
        )
    else:
        columns[f"{phase}_share_basis"] = "Share source"
    columns[f"{phase}_snap_share"] = "Snap share"
    return columns


def render_players(season: int) -> None:
    st.header("Player opportunity")
    grain = st.radio("View", ["Season", "Game"], horizontal=True, key="opportunity_view")
    season_view = grain == "Season"
    table = "player_season_opportunity" if season_view else "player_game_opportunity"
    path = opportunity_path(table, season)
    if not path.is_file():
        st.info(f"Build the player marts with `make opportunity SEASON={season}`.")
        return

    frame = pl.scan_parquet(path)
    options = (
        frame.select(
            pl.col("team_id").unique().sort().implode(), pl.col("role").unique().sort().implode()
        )
        .collect()
        .row(0)
    )
    filters = st.columns(3)
    teams = filters[0].multiselect("Teams", options[0])
    roles = filters[1].multiselect("Roles", options[1])
    name = filters[2].text_input("Player name or ID")
    if teams:
        frame = frame.filter(pl.col("team_id").is_in(teams))
    if roles:
        frame = frame.filter(pl.col("role").is_in(roles))
    if name.strip():
        query = name.strip().lower()
        frame = frame.filter(
            pl.col("player").str.to_lowercase().str.contains(query, literal=True)
            | pl.col("player_id").str.to_lowercase().str.contains(query, literal=True)
        )

    base = {"player": "Player", "team_id": "Team", "role": "Role"}
    if season_view:
        base.update({"player_games": "Player games", "team_games": "Team games"})
    else:
        weeks = frame.select(pl.col("week").unique().sort()).collect()["week"].to_list()
        week = st.selectbox("Week", ["All"] + [str(value) for value in weeks])
        if week != "All":
            frame = frame.filter(pl.col("week") == int(week))
        base.update({"week": "Week", "opponent_team_id": "Opponent", "season_type": "Season stage"})

    metric = st.radio(
        "Metric",
        [*PHASES, "on_field"],
        format_func=lambda value: {
            **PHASE_LABELS,
            "on_field": "On-field plays",
        }[value],
        horizontal=True,
        key="opportunity_metric",
    )
    if metric == "on_field":
        columns = {
            f"{side}_{measure}": f"{PHASE_LABELS[side]} {label}"
            for side in SIDES
            for measure, label in (
                ("on_field", "on-field plays"),
                ("covered_plays", "covered plays"),
                ("expected_plays", "eligible plays"),
            )
        }
        st.caption(ON_FIELD_NOTE)
        sort = "offense_on_field"
    else:
        columns = _snap_columns(metric, season_view)
        st.caption(SNAP_NOTE)
        sort = f"snaps_{metric}"

    fields = {**base, **columns}
    result = frame.select(*fields, "player_id", "season", *([] if season_view else ["game_id"]))
    display = result.sort(sort, descending=True, nulls_last=True).collect()
    if display.is_empty():
        st.info("No players match these filters.")
        return

    share = f"{metric}_snap_share"
    visible = display.select(*fields)
    formats = {}
    if share in fields:
        visible = visible.with_columns(pl.col(share) * 100)
        formats[fields[share]] = st.column_config.NumberColumn(format="%.1f%%")
    st.dataframe(visible.rename(fields), hide_index=True, column_config=formats)

    source = attribution_block([Source.NFLVERSE, Source.PFR, participation_source(season)])
    st.download_button(
        "Export filtered CSV",
        display.with_columns(
            claim_type=pl.lit("descriptive"),
            attribution=pl.lit(source),
            limitation=pl.lit(ON_FIELD_NOTE if metric == "on_field" else SNAP_NOTE),
        ).write_csv(),
        file_name=f"player_opportunity_{season}_{grain.lower()}_{metric}.csv",
        mime="text/csv",
    )
    st.caption("Descriptive opportunity and participation coverage")
    st.text(source)
