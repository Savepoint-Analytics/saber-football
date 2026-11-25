"""Streamlit views for observed weekly EPA and adjusted season efficiency."""

from __future__ import annotations

import json

import polars as pl
import streamlit as st

from src.analytics.team_efficiency import efficiency_metadata_path, efficiency_path
from src.compliance.attributions import Source, attribution_for

WEEKLY_METRICS = {
    "offensive_epa_per_play": "Offense EPA per play",
    "defensive_epa_allowed_per_play": "Defense EPA allowed per play",
}
ADJUSTED_NOTE = (
    "Regular-season estimates account for opponents and venue. Positive values indicate stronger "
    "performance relative to the league, including on defense. Intervals use a 90% game bootstrap."
)


def _show_trends(weekly: pl.DataFrame) -> None:
    metric = st.selectbox("Measure", list(WEEKLY_METRICS), format_func=WEEKLY_METRICS.__getitem__)
    label = WEEKLY_METRICS[metric]
    rename = {
        "week": "Week",
        "team_id": "Team",
        "opponent_team_id": "Opponent",
        "season_type": "Season stage",
        metric: label,
        "offensive_plays": "Offense plays",
        "defensive_plays": "Defense plays",
    }
    shown = weekly.select(*rename).rename(rename)
    st.line_chart(shown, x="Week", y=label, color="Team")
    if metric == "defensive_epa_allowed_per_play":
        st.caption("Lower EPA allowed per play is better.")
    st.dataframe(
        shown, hide_index=True, column_config={label: st.column_config.NumberColumn(format="%.3f")}
    )


def _show_ratings(ratings: pl.DataFrame, validation: dict[str, float]) -> None:
    st.caption(ADJUSTED_NOTE)
    phase = st.radio(
        "Rating",
        ["net", "offense", "defense"],
        horizontal=True,
        format_func={"net": "Overall", "offense": "Offense", "defense": "Defense"}.__getitem__,
    )
    metric = f"{phase}_adjusted_epa"
    columns = {
        "team_id": "Team",
        metric: "Adjusted EPA/play",
        f"{metric}_p05": "90% low",
        f"{metric}_p95": "90% high",
        "games": "Games",
        "offensive_plays": "Offense plays",
        "defensive_plays": "Defense plays",
    }
    st.dataframe(
        ratings.sort(metric, descending=True).select(*columns).rename(columns),
        hide_index=True,
        column_config={
            name: st.column_config.NumberColumn(format="%.3f")
            for name in ("Adjusted EPA/play", "90% low", "90% high")
        },
    )
    if validation.get("games", 0):
        baseline = validation["offense_only_weighted_rmse"]
        adjusted = validation["opponent_adjusted_weighted_rmse"]
        st.caption(
            f"Walk-forward validation over {validation['games']:.0f} games from week 5 onward. "
            f"Adjusted EPA/play RMSE {adjusted:.3f} · Offense-only baseline {baseline:.3f}. "
            "Lower error is better."
        )


def render_team_trends(season: int) -> None:
    st.header("Team trends and efficiency")
    weekly_path = efficiency_path("team_weekly", season)
    ratings_path = efficiency_path("team_adjusted_efficiency", season)
    if not weekly_path.is_file() or not ratings_path.is_file():
        st.info(f"Build team trends with `make team-trends SEASON={season}`.")
        return

    grain = st.radio(
        "View",
        ["Weekly trends", "Opponent-adjusted efficiency"],
        horizontal=True,
        key="team_trends_view",
    )
    weekly = pl.read_parquet(weekly_path)
    ratings = pl.read_parquet(ratings_path)
    teams = weekly["team_id"].unique().sort().to_list()
    if not teams:
        st.info("No eligible plays for this season.")
        return

    if grain == "Weekly trends":
        selected = st.multiselect("Teams", teams, default=teams[:2])
        weekly = weekly.filter(pl.col("team_id").is_in(selected))
        st.caption(
            "Observed EPA uses non-special-teams plays with a pass or rush flag and an EPA value."
        )
        if weekly.is_empty():
            st.info("Select a team to see its weekly results.")
            return
        _show_trends(weekly)
        export, slug = weekly, "team_weekly"
        limitation = "Observed EPA on eligible pass and rush plays."
    else:
        selected = st.multiselect("Teams", teams)
        if selected:
            ratings = ratings.filter(pl.col("team_id").is_in(selected))
        path = efficiency_metadata_path(season)
        scores = (
            json.loads(path.read_text(encoding="utf-8"))["walk_forward_validation"]
            if path.is_file()
            else {}
        )
        _show_ratings(ratings, scores)
        export, slug, limitation = ratings, "team_adjusted_efficiency", ADJUSTED_NOTE

    source = attribution_for(Source.NFLVERSE)
    st.download_button(
        "Export filtered CSV",
        export.with_columns(
            claim_type=pl.lit("descriptive"),
            attribution=pl.lit(source),
            limitation=pl.lit(limitation),
        ).write_csv(),
        file_name=f"{slug}_{season}.csv",
        mime="text/csv",
    )
    st.caption(source)
