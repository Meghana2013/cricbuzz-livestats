"""CRUD page: create, read, update and delete player records."""
import sqlite3
from datetime import date

import streamlit as st

from services import player_service as svc

st.set_page_config(page_title="CRUD Operations", page_icon="🛠️", layout="wide")
st.title("🛠️ CRUD Operations: Players")


def safe_call(action, success_message: str) -> bool:
    """Run action(); show friendly errors; return True on success."""
    try:
        action()
    except svc.ValidationError as exc:
        st.error(str(exc))
        return False
    except sqlite3.Error as exc:
        st.error(f"Database error: {exc}")
        return False
    st.success(success_message)
    return True


def player_label(row) -> str:
    return f"{row.full_name}  ({row.country}, {row.playing_role})  #{row.player_id}"


tab_read, tab_create, tab_update, tab_delete, tab_stats = st.tabs(
    ["Read", "Create", "Update", "Delete", "Career stats"])

# ------------------------------------------------------------------- READ
with tab_read:
    c1, c2, c3 = st.columns(3)
    search = c1.text_input("Search by name")
    country = c2.selectbox("Country", [""] + svc.list_countries(), format_func=lambda x: x or "All")
    role = c3.selectbox("Role", [""] + svc.ROLES, format_func=lambda x: x or "All")
    players = svc.list_players(search, country, role)
    st.write(f"**{len(players)} players**")
    st.dataframe(players, hide_index=True)

# ----------------------------------------------------------------- CREATE
with tab_create:
    with st.form("create_form", clear_on_submit=True):
        name = st.text_input("Full name *")
        country_new = st.text_input("Country *")
        role_new = st.selectbox("Playing role *", svc.ROLES)
        bat_new = st.selectbox("Batting style", svc.BATTING_STYLES)
        bowl_new = st.selectbox("Bowling style", ["(none)"] + svc.BOWLING_STYLES)
        dob_new = st.date_input("Date of birth", value=date(2000, 1, 1),
                                min_value=date(1940, 1, 1), max_value=date.today())
        submitted = st.form_submit_button("Add player", type="primary")
    if submitted:
        safe_call(lambda: svc.create_player(
            name, country_new, role_new, bat_new,
            None if bowl_new == "(none)" else bowl_new, dob_new), "Player added.")

# ----------------------------------------------------------------- UPDATE
with tab_update:
    all_players = svc.list_players()
    options = {player_label(r): int(r.player_id) for r in all_players.itertuples()}
    picked = st.selectbox("Choose a player to edit", list(options), key="upd_pick")
    pid = options[picked]
    current = svc.get_player(pid)
    with st.form(f"update_form_{pid}"):
        u_name = st.text_input("Full name", current["full_name"])
        u_country = st.text_input("Country", current["country"])
        u_role = st.selectbox("Playing role", svc.ROLES, index=svc.ROLES.index(current["playing_role"]))
        bat_opts = svc.BATTING_STYLES
        u_bat = st.selectbox("Batting style", bat_opts,
                             index=bat_opts.index(current["batting_style"]) if current["batting_style"] in bat_opts else 0)
        bowl_opts = ["(none)"] + svc.BOWLING_STYLES
        u_bowl = st.selectbox("Bowling style", bowl_opts,
                              index=bowl_opts.index(current["bowling_style"]) if current["bowling_style"] in bowl_opts else 0)
        dob_current = date.fromisoformat(current["date_of_birth"]) if current["date_of_birth"] else date(2000, 1, 1)
        u_dob = st.date_input("Date of birth", dob_current, min_value=date(1940, 1, 1), max_value=date.today())
        save = st.form_submit_button("Save changes", type="primary")
    if save:
        safe_call(lambda: svc.update_player(
            pid, full_name=u_name, country=u_country, playing_role=u_role, batting_style=u_bat,
            bowling_style=None if u_bowl == "(none)" else u_bowl, date_of_birth=u_dob), "Player updated.")

# ----------------------------------------------------------------- DELETE
with tab_delete:
    all_players = svc.list_players()
    del_options = {player_label(r): int(r.player_id) for r in all_players.itertuples()}
    del_pick = st.selectbox("Choose a player to delete", list(del_options), key="del_pick")
    del_id = del_options[del_pick]
    usage = svc.player_usage(del_id)
    st.warning("Deleting also removes linked records: " +
               ", ".join(f"{n} {label}" for label, n in usage.items()))
    confirm = st.checkbox("I understand this cannot be undone", key=f"confirm_{del_id}")
    if st.button("Delete player", disabled=not confirm, type="primary"):
        if safe_call(lambda: svc.delete_player(del_id), "Player deleted."):
            st.info("Open the Read tab to see the updated list.")

# ----------------------------------------------------------- CAREER STATS
with tab_stats:
    all_players = svc.list_players()
    st_options = {player_label(r): int(r.player_id) for r in all_players.itertuples()}
    st_pick = st.selectbox("Choose a player", list(st_options), key="stats_pick")
    st_id = st_options[st_pick]
    st.dataframe(svc.get_career_stats(st_id), hide_index=True)
    with st.form(f"stats_form_{st_id}"):
        fmt = st.selectbox("Format", svc.FORMATS)
        g1, g2, g3, g4 = st.columns(4)
        matches = g1.number_input("Matches", 0, 1000, 0)
        innings = g2.number_input("Innings", 0, 1000, 0)
        runs = g3.number_input("Runs", 0, 50000, 0)
        hs = g4.number_input("Highest score", 0, 500, 0)
        h1, h2, h3, h4 = st.columns(4)
        avg = h1.number_input("Batting average", 0.0, 200.0, 0.0)
        sr = h2.number_input("Strike rate", 0.0, 300.0, 0.0)
        hundreds = h3.number_input("Centuries", 0, 100, 0)
        fifties = h4.number_input("Fifties", 0, 300, 0)
        k1, k2 = st.columns(2)
        wickets = k1.number_input("Wickets", 0, 2000, 0)
        catches = k2.number_input("Catches", 0, 1000, 0)
        go = st.form_submit_button("Save career stats (adds or updates the row)", type="primary")
    if go:
        safe_call(lambda: svc.upsert_career_stats(
            st_id, fmt, int(matches), int(innings), int(runs), int(hs), float(avg), float(sr),
            int(hundreds), int(fifties), int(wickets), int(catches)), "Career stats saved.")
