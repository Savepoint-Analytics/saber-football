"""NFL team and player analytics dashboard."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.analytics.team_style import team_style_output_path
from src.compliance.attributions import Source, attribution_block, attribution_for

DEFAULT_SEASON = 2025
CLAIM_TYPE = "descriptive"
LIMITATION = "EPA and WPA are nflverse model estimates. Team metrics use observed results."
DISPLAY_COLUMNS = [
    "team_id",
    "games",
    "wins",
    "point_diff_per_game",
    "total_epa_per_game",
    "offensive_epa_per_play",
    "defensive_epa_allowed_per_game",
    "success_rate",
    "explosive_rate",
    "pass_rate_over_expected",
    "turnover_margin_per_game",
    "plays_per_game",
]


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - optional serving extra
        raise RuntimeError("Install serving extras before running the dashboard.") from exc

    st.set_page_config(page_title="Savepoint Football Analytics", layout="wide")
    st.title("Savepoint Football Analytics")

    page = st.sidebar.radio(
        "Dashboard", ["Team style", "Player opportunity", "Team trends"], key="dashboard_page"
    )
    season = int(
        st.sidebar.number_input("Season", min_value=1999, max_value=2100, value=DEFAULT_SEASON)
    )
    if page == "Player opportunity":
        from src.serving.player_view import render_players

        render_players(season)
        return
    if page == "Team trends":
        from src.serving.team_trends import render_team_trends

        render_team_trends(season)
        return

    st.caption("NFL team efficiency and style from nflverse EPA/WPA.")
    path = team_style_output_path(season)
    if not Path(path).exists():
        st.warning(
            f"No team-style mart found for {season}. Run `make core analytics SEASON={season}`."
        )
        return

    df = pl.read_parquet(path)
    max_games = df["games"].max()
    if not isinstance(max_games, int) or max_games < 1:
        st.warning(f"No team games available for {season}.")
        return

    teams = df["team_id"].sort().to_list()
    selected_teams = st.sidebar.multiselect("Teams", teams, default=teams)
    min_games = 1
    if max_games > 1:
        min_games = st.sidebar.slider("Minimum Games", min_value=1, max_value=max_games, value=1)
    sort_metric = st.sidebar.selectbox(
        "Sort",
        [
            "total_epa_per_game",
            "point_diff_per_game",
            "offensive_epa_per_play",
            "success_rate",
            "explosive_rate",
            "pass_rate_over_expected",
        ],
    )

    filtered = df.filter(
        pl.col("team_id").is_in(selected_teams) & (pl.col("games") >= min_games)
    ).sort(sort_metric, descending=True)
    if filtered.is_empty():
        st.warning("No teams match the current filters.")
        return
    pdf = filtered.to_pandas()

    top_line = st.columns(4)
    top_line[0].metric("Teams", f"{filtered.height}")
    top_line[1].metric("Avg EPA/Game", f"{pdf['total_epa_per_game'].mean():.2f}")
    top_line[2].metric("Avg Success", f"{pdf['success_rate'].mean():.1%}")
    top_line[3].metric("Avg Explosive", f"{pdf['explosive_rate'].mean():.1%}")

    st.subheader("Efficiency And Style")
    st.dataframe(pdf[DISPLAY_COLUMNS], use_container_width=True, hide_index=True)
    st.download_button(
        "Export CSV",
        data=filtered.select(DISPLAY_COLUMNS)
        .with_columns(
            season=pl.lit(season),
            claim_type=pl.lit(CLAIM_TYPE),
            attribution=pl.lit(attribution_for(Source.NFLVERSE)),
            limitation=pl.lit(LIMITATION),
        )
        .write_csv(),
        file_name=f"team_style_{season}.csv",
        mime="text/csv",
    )

    st.subheader("Offensive Efficiency vs. Explosiveness")
    try:
        import plotly.express as px
    except ImportError:
        st.scatter_chart(pdf, x="offensive_epa_per_play", y="explosive_rate", color="team_id")
    else:
        fig = px.scatter(
            pdf,
            x="offensive_epa_per_play",
            y="explosive_rate",
            color="team_id",
            size="plays_per_game",
            hover_data=["wins", "success_rate", "pass_rate_over_expected"],
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Source And Limitations")
    st.text(attribution_block([Source.NFLVERSE]))
    st.caption(f"Claim type — {CLAIM_TYPE}. {LIMITATION}")


if __name__ == "__main__":
    main()
