"""Team efficiency/style dashboard."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.analytics.team_style import team_style_output_path

DEFAULT_SEASON = 2025


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:  # pragma: no cover - optional serving extra
        raise RuntimeError("Install serving extras before running the dashboard.") from exc

    st.set_page_config(page_title="Savepoint Football Analytics", layout="wide")
    st.title("Savepoint Football Analytics")
    st.caption("NFL team efficiency and style from nflverse EPA/WPA.")

    season = st.sidebar.number_input("Season", min_value=1999, max_value=2100, value=DEFAULT_SEASON)
    path = team_style_output_path(int(season))
    if not Path(path).exists():
        st.warning(f"No team-style mart found for {season}. Run `make core analytics SEASON={season}`.")
        return

    df = pl.read_parquet(path).sort("total_epa_per_game", descending=True)
    pdf = df.to_pandas()

    top_line = st.columns(4)
    top_line[0].metric("Teams", f"{df.height}")
    top_line[1].metric("Avg EPA/Game", f"{df['total_epa_per_game'].mean():.2f}")
    top_line[2].metric("Avg Success", f"{df['success_rate'].mean():.1%}")
    top_line[3].metric("Avg Explosive", f"{df['explosive_rate'].mean():.1%}")

    st.subheader("Efficiency And Style")
    st.dataframe(
        pdf[
            [
                "team_id",
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
        ],
        use_container_width=True,
        hide_index=True,
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


if __name__ == "__main__":
    main()
