"""Cricbuzz LiveStats Analytics: home page (entry point).

Run with:  streamlit run main.py
"""
import streamlit as st

import config
from utils.db_connection import DB_PATH, fetch_df

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #f5f7f9; }
    div[data-testid="stMetric"] {
        background: #ffffff; padding: 14px 18px; border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏏 Cricbuzz LiveStats")
st.caption("Real-time cricket data, SQL analytics and data management in one dashboard.")

# ----------------------------------------------------------- sidebar status
with st.sidebar:
    st.header("Project status")
    st.write("Database:", "✅ found" if DB_PATH.exists() else "❌ missing")
    st.write("API key:", "✅ configured" if config.RAPIDAPI_KEY else "❌ missing (.env)")
    st.info("Sample database data is synthetic (for SQL practice). "
            "Live pages use real Cricbuzz API data.")

# ------------------------------------------------------------ database stats
if not DB_PATH.exists():
    st.error("Database not found. Run: python scripts\\setup_database.py --reset  then  "
             "python scripts\\seed_data.py")
    st.stop()

try:
    counts = fetch_df(
        "SELECT (SELECT COUNT(*) FROM players) AS players, "
        "(SELECT COUNT(*) FROM teams) AS teams, "
        "(SELECT COUNT(*) FROM matches) AS matches, "
        "(SELECT COUNT(*) FROM venues) AS venues"
    ).iloc[0]
except Exception as exc:  # database exists but tables are missing/corrupt
    st.error(f"Could not read the database: {exc}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", int(counts["players"]))
c2.metric("Teams", int(counts["teams"]))
c3.metric("Matches", int(counts["matches"]))
c4.metric("Venues", int(counts["venues"]))

st.subheader("What you can do here")
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "**📡 Live Matches** — current and recent matches from the Cricbuzz API.\n\n"
        "**⭐ Top Players** — leading batters and bowlers.")
with col_b:
    st.markdown(
        "**🧮 SQL Analytics** — 25 questions from beginner to advanced, plus a custom SQL box.\n\n"
        "**🛠️ CRUD Operations** — add, edit and delete player records safely.")
st.write("Use the sidebar menu to open a page.")

with st.expander("Technologies used"):
    st.write("Python · Streamlit · SQLite · pandas · Cricbuzz API (RapidAPI) · python-dotenv")
