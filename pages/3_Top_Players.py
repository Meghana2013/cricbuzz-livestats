"""Top Players page: official rankings from the API and top performers from the database."""
import pandas as pd
import plotly.express as px
import streamlit as st

from api.cricbuzz_client import ApiError, CricbuzzClient
from utils.db_connection import fetch_df

st.set_page_config(page_title="Top Players", page_icon="🌟", layout="wide")
st.title("🌟 Top Players")

tab_api, tab_runs, tab_wickets = st.tabs(
    ["🌍 Official rankings (API)", "🏏 Top run scorers (database)", "🎯 Top wicket takers (database)"])


@st.cache_data(ttl=600, show_spinner=False)
def load_rankings(category: str, fmt: str) -> dict:
    return CricbuzzClient().get(f"/stats/v1/rankings/{category}", {"formatType": fmt})


with tab_api:
    c1, c2 = st.columns(2)
    category = c1.selectbox("Category", ["batsmen", "bowlers"])
    fmt = c2.selectbox("Format", ["test", "odi", "t20"], index=1)
    try:
        with st.spinner("Loading rankings..."):
            data = load_rankings(category, fmt)
        df = pd.DataFrame(data.get("rank") or [])
        if df.empty:
            st.info("The API returned no rankings for this selection.")
        else:
            wanted = [c for c in ["rank", "name", "country", "rating", "points", "trend"] if c in df]
            top = df[wanted].head(15).copy()
            st.dataframe(top, hide_index=True)
            if "rating" in top and "name" in top:
                top["rating"] = pd.to_numeric(top["rating"], errors="coerce")
                st.plotly_chart(px.bar(top.dropna(subset=["rating"]), x="name", y="rating",
                                       title=f"Top 15 {category} ({fmt.upper()})"))
    except ApiError as exc:
        st.warning(f"Rankings are unavailable right now: {exc}")

st.sidebar.info("Database numbers on this page are synthetic sample data. "
                "The rankings tab uses real API data.")


def top_table(order_column: str, columns: str, fmt_name: str, limit: int) -> pd.DataFrame:
    sql = (f"SELECT p.full_name AS player, p.country, {columns} "
           "FROM player_career_stats s JOIN players p ON p.player_id = s.player_id "
           f"WHERE s.match_format = ? ORDER BY {order_column} DESC LIMIT ?")
    return fetch_df(sql, [fmt_name, limit])


with tab_runs:
    c1, c2 = st.columns(2)
    fmt_name = c1.selectbox("Format", ["Test", "ODI", "T20I"], index=1, key="runs_fmt")
    limit = c2.slider("How many players", 5, 25, 10, key="runs_n")
    try:
        df = top_table("s.runs", "s.runs, s.batting_avg, s.centuries", fmt_name, limit)
        st.dataframe(df, hide_index=True)
        st.plotly_chart(px.bar(df, x="player", y="runs", color="batting_avg",
                               title=f"Top {limit} run scorers ({fmt_name})"))
    except Exception as exc:
        st.error(f"Database problem: {exc}")

with tab_wickets:
    c1, c2 = st.columns(2)
    fmt_name = c1.selectbox("Format", ["Test", "ODI", "T20I"], index=1, key="wk_fmt")
    limit = c2.slider("How many players", 5, 25, 10, key="wk_n")
    try:
        df = top_table("s.wickets", "s.wickets, s.bowling_avg, s.economy", fmt_name, limit)
        st.dataframe(df, hide_index=True)
        st.plotly_chart(px.bar(df, x="player", y="wickets", color="economy",
                               title=f"Top {limit} wicket takers ({fmt_name})"))
    except Exception as exc:
        st.error(f"Database problem: {exc}")
