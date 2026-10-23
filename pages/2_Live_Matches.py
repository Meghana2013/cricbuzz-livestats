"""Live Matches page: live and recent matches (and scorecards) from the Cricbuzz API."""
from datetime import datetime

import pandas as pd
import streamlit as st

from api.cricbuzz_client import ApiError, CricbuzzClient

st.set_page_config(page_title="Live Matches", page_icon="📡", layout="wide")
st.title("📡 Live Matches")
st.caption("Real data from the Cricbuzz API (RapidAPI). Results are cached for 60 seconds to save API quota.")


@st.cache_data(ttl=60, show_spinner=False)
def load_matches(kind: str) -> dict:
    """Fetch /matches/v1/<kind> (live or recent)."""
    return CricbuzzClient().get(f"/matches/v1/{kind}")


@st.cache_data(ttl=300, show_spinner=False)
def load_scorecard(match_id: int) -> dict:
    """Fetch the full scorecard of one match."""
    return CricbuzzClient().get(f"/mcenter/v1/{match_id}/scard")


def format_score(team_score: dict) -> str:
    """Turn {'inngs1': {'runs': 165, 'wickets': 6, 'overs': 20.0}} into '165/6 (20)'."""
    parts = []
    for key in sorted(team_score or {}):
        inn = team_score[key] or {}
        if inn.get("runs") is None:
            continue
        wickets = inn.get("wickets", 10)
        overs = inn.get("overs")
        parts.append(f"{inn['runs']}/{wickets}" + (f" ({overs})" if overs is not None else ""))
    return " & ".join(parts) if parts else "Yet to bat"


def start_date(info: dict) -> str:
    try:
        return datetime.fromtimestamp(int(info["startDate"]) / 1000).strftime("%d %b %Y")
    except (KeyError, TypeError, ValueError, OSError):
        return ""


def parse_matches(data: dict) -> list:
    """Flatten typeMatches -> seriesMatches -> matches into simple dicts."""
    rows = []
    for type_block in data.get("typeMatches") or []:
        for series_block in type_block.get("seriesMatches") or []:
            wrapper = series_block.get("seriesAdWrapper")
            if not wrapper:
                continue
            for item in wrapper.get("matches") or []:
                info = item.get("matchInfo") or {}
                score = item.get("matchScore") or {}
                team1, team2 = info.get("team1") or {}, info.get("team2") or {}
                venue = info.get("venueInfo") or {}
                rows.append({
                    "match_id": info.get("matchId"),
                    "series": wrapper.get("seriesName", ""),
                    "desc": info.get("matchDesc", ""),
                    "format": info.get("matchFormat", ""),
                    "team1": team1.get("teamName", "Team 1"),
                    "team2": team2.get("teamName", "Team 2"),
                    "score1": format_score(score.get("team1Score")),
                    "score2": format_score(score.get("team2Score")),
                    "status": info.get("status", ""),
                    "venue": ", ".join(x for x in (venue.get("ground"), venue.get("city")) if x),
                    "date": start_date(info),
                })
    return rows


def show_scorecard(data: dict) -> None:
    """Render batting and bowling tables for each innings."""
    st.write("**Result:**", data.get("status", ""))
    for innings in data.get("scorecard") or []:
        st.markdown(f"##### {innings.get('batteamname', 'Innings')}: "
                    f"{innings.get('score')}/{innings.get('wickets')} ({innings.get('overs')} ov)")
        bat = pd.DataFrame(innings.get("batsman") or [])
        bowl = pd.DataFrame(innings.get("bowler") or [])
        if not bat.empty:
            cols = [c for c in ["name", "runs", "balls", "fours", "sixes", "strkrate", "outdec"] if c in bat]
            st.dataframe(bat[cols], hide_index=True)
        if not bowl.empty:
            cols = [c for c in ["name", "overs", "maidens", "runs", "wickets", "economy"] if c in bowl]
            st.dataframe(bowl[cols], hide_index=True)


kind_label = st.radio("Show", ["Live now", "Recent results"], horizontal=True)
kind = "live" if kind_label == "Live now" else "recent"

try:
    with st.spinner("Fetching matches..."):
        raw = load_matches(kind)
except ApiError as exc:
    st.error(f"Could not load matches: {exc}")
    st.stop()

matches = parse_matches(raw)
if not matches:
    st.info("No matches to show right now. Try 'Recent results'.")
    st.stop()

formats = sorted({m["format"] for m in matches if m["format"]})
chosen = st.multiselect("Filter by format", formats, default=formats)
shown = [m for m in matches if not chosen or m["format"] in chosen]
st.metric("Matches", len(shown))

for m in shown:
    with st.container(border=True):
        st.subheader(f"{m['team1']} vs {m['team2']}")
        st.caption(f"{m['series']} · {m['desc']} · {m['format']}"
                   + (f" · {m['date']}" if m["date"] else ""))
        c1, c2 = st.columns(2)
        c1.write(f"**{m['team1']}**  {m['score1']}")
        c2.write(f"**{m['team2']}**  {m['score2']}")
        st.write(f"🏁 {m['status']}")
        if m["venue"]:
            st.caption(f"📍 {m['venue']}")
        with st.expander("Scorecard"):
            if st.button("Load scorecard", key=f"sc_{kind}_{m['match_id']}"):
                try:
                    show_scorecard(load_scorecard(int(m["match_id"])))
                except (ApiError, TypeError, ValueError) as exc:
                    st.error(f"Scorecard not available: {exc}")
