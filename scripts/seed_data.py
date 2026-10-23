"""Seed the database with SYNTHETIC sample data for SQL practice.

IMPORTANT: player names, scores and results generated here are fictional.
They are NOT real cricket statistics. Live pages use real API data.
Venue names and countries are real; capacities are approximate.

Usage:
    python scripts/setup_database.py --reset
    python scripts/seed_data.py
"""
import itertools
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.db_connection import db_session  # noqa: E402

random.seed(42)
TODAY = date.today()
START = date(2022, 1, 15)
N_SERIES = 160

TEAMS = [
    ("India", "India", "IND"), ("Australia", "Australia", "AUS"),
    ("England", "England", "ENG"), ("Pakistan", "Pakistan", "PAK"),
    ("South Africa", "South Africa", "SA"), ("New Zealand", "New Zealand", "NZ"),
    ("Sri Lanka", "Sri Lanka", "SL"), ("Bangladesh", "Bangladesh", "BAN"),
    ("West Indies", "West Indies", "WI"), ("Afghanistan", "Afghanistan", "AFG"),
]

# (name, city, country, approximate capacity)
VENUES = [
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000),
    ("Eden Gardens", "Kolkata", "India", 66000),
    ("Rajiv Gandhi International Stadium", "Hyderabad", "India", 55000),
    ("Wankhede Stadium", "Mumbai", "India", 33000),
    ("Melbourne Cricket Ground", "Melbourne", "Australia", 100000),
    ("Sydney Cricket Ground", "Sydney", "Australia", 48000),
    ("Lord's", "London", "England", 31000),
    ("Gaddafi Stadium", "Lahore", "Pakistan", 34000),
    ("Newlands", "Cape Town", "South Africa", 25000),
    ("Eden Park", "Auckland", "New Zealand", 42000),
    ("Galle International Stadium", "Galle", "Sri Lanka", 35000),
    ("Shere Bangla National Stadium", "Dhaka", "Bangladesh", 25000),
    ("Kensington Oval", "Bridgetown", "West Indies", 28000),
    ("Dubai International Cricket Stadium", "Dubai", "United Arab Emirates", 25000),
    ("Sharjah Cricket Stadium", "Sharjah", "United Arab Emirates", 17000),
]

FIRST = ["Aarav", "Vihaan", "Arjun", "Rohan", "Kabir", "Ishaan", "Dev", "Neel", "Karan", "Sameer",
         "Imran", "Hamza", "Bilal", "Faisal", "Omar", "Zain", "Tariq", "Liam", "Noah", "Jack",
         "Oliver", "Harry", "Ryan", "Cameron", "Jacob", "Ethan", "Kyle", "Dean", "Pieter", "Sipho",
         "Thabo", "Lahiru", "Kusal", "Dimuth", "Rashid", "Nasir", "Mehedi", "Shakib", "Darren", "Jason"]
LAST = ["Verma", "Iyer", "Nair", "Reddy", "Kapoor", "Mehta", "Khan", "Ahmed", "Malik", "Butt",
        "Raza", "Fraser", "Taylor", "Brown", "Wilson", "Clarke", "Walker", "Hughes", "Cooper", "Bailey",
        "Marais", "Botha", "Naidoo", "Perera", "Silva", "Fernando", "Hossain", "Rahman", "Karim", "Ali",
        "Holder", "Pooran", "Hope", "Gayle", "Shah", "Noori", "Zadran", "Stirling", "Hart", "Reid"]

ROLE_PLAN = ["Batsman"] * 5 + ["Wicket-keeper"] * 2 + ["All-rounder"] * 3 + ["Bowler"] * 6
BAT_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWL_STYLES = {
    "Bowler": ["Right-arm fast", "Left-arm fast", "Right-arm medium", "Legbreak", "Left-arm orthodox"],
    "All-rounder": ["Right-arm medium", "Right-arm offbreak", "Left-arm orthodox", "Legbreak"],
    "Batsman": [None],
    "Wicket-keeper": [None],
}

FORMATS = ["T20I", "ODI", "Test"]
MEAN_BALLS = {"T20I": (22, 14, 6), "ODI": (45, 32, 12), "Test": (80, 55, 22)}
BASE_SR = {"T20I": 135, "ODI": 90, "Test": 50}
EXTRAS_RANGE = {"T20I": (2, 12), "ODI": (4, 16), "Test": (5, 30)}
HOME_COUNTRIES = {"India", "Australia", "England", "Pakistan", "South Africa",
                  "New Zealand", "Sri Lanka", "Bangladesh", "West Indies"}


def ordinal(n):
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def overs_notation(balls):
    return balls // 6 + (balls % 6) / 10


def bat_factor(player, match_date):
    years = (match_date - START).days / 365.0
    return min(1.8, max(0.5, player["bat_skill"] * (1 + player["slope"] * years)))


# ----------------------------------------------------------------- simulation
def simulate_batting(xi, fmt, match_date, home_boost, ball_limit, target=None):
    """Simulate one innings; returns rows, extras, total, wickets, balls."""
    extras = random.randint(*EXTRAS_RANGE[fmt])
    need = None if target is None else target + 1 - extras
    rows, balls_left, total, wickets = [], ball_limit, 0, 0
    for pos, p in enumerate(xi, start=1):
        if balls_left <= 0:
            break
        f = bat_factor(p, match_date) * home_boost
        bucket = 0 if pos <= 3 else (1 if pos <= 7 else 2)
        mean_balls = MEAN_BALLS[fmt][bucket] * (0.7 + 0.3 * f)
        draw = max(1, int(random.expovariate(1.0 / mean_balls)))
        balls = min(draw, balls_left)
        runs = max(0, int(balls * BASE_SR[fmt] / 100 * f * max(0.1, random.gauss(1, 0.35))))
        is_out = draw <= balls_left and pos < 11
        done = False
        if need is not None and total + runs >= need:
            runs = max(0, need - total)
            is_out, done = False, True
        sixes = int(runs * random.uniform(0, 0.2) / 6) if fmt != "Test" else int(runs * random.uniform(0, 0.08) / 6)
        fours = int((runs - 6 * sixes) * random.uniform(0.1, 0.45) / 4)
        rows.append({"player": p, "pos": pos, "runs": runs, "balls": balls, "fours": fours,
                     "sixes": sixes, "out": is_out, "desc": None})
        balls_left -= balls
        total += runs
        if is_out:
            wickets += 1
        if done or wickets >= 10:
            break
    return {"rows": rows, "extras": extras, "total": total + extras, "wickets": wickets,
            "balls": sum(r["balls"] for r in rows)}


def simulate_bowling(bowl_xi, innings, fmt, match_date):
    """Spread overs, runs and wickets of one innings across the bowling side."""
    bowlers = [p for p in bowl_xi if p["role"] == "Bowler"]
    ars = [p for p in bowl_xi if p["role"] == "All-rounder"]
    attack = bowlers + random.sample(ars, 1)
    n = len(attack)
    total_balls = max(innings["balls"], 6)

    if fmt == "Test":
        weights = [random.uniform(0.7, 1.3) for _ in attack]
        balls = [max(6, int(total_balls * w / sum(weights))) for w in weights]
    else:
        base, rem = divmod(total_balls, n)
        balls = [base + (1 if i < rem else 0) for i in range(n)]

    weights = [b * (1.4 - 0.3 * p["bowl_skill"]) * random.uniform(0.85, 1.15) for b, p in zip(balls, attack)]
    runs = [int(innings["total"] * w / sum(weights)) for w in weights]
    runs[0] += innings["total"] - sum(runs)

    wickets = [0] * n
    wk_weights = [b * p["bowl_skill"] for b, p in zip(balls, attack)]
    for row in innings["rows"]:
        if not row["out"]:
            continue
        if random.random() < 0.12:
            row["desc"] = "run out"
            continue
        i = random.choices(range(n), weights=wk_weights)[0]
        wickets[i] += 1
        row["desc"] = random.choice(["bowled", "caught", "caught", "lbw"])

    out = []
    for p, b, r, w in zip(attack, balls, runs, wickets):
        out.append({"player": p, "balls": b, "runs": max(0, r), "wickets": w,
                    "maidens": random.choice([0, 0, 0, 1]) if fmt != "T20I" else 0})
    return out


def pick_xi(squad):
    by_role = {}
    for p in squad:
        by_role.setdefault(p["role"], []).append(p)
    bats = sorted(random.sample(by_role["Batsman"], 4), key=lambda p: p["order"])
    wk = random.sample(by_role["Wicket-keeper"], 1)
    ars = sorted(random.sample(by_role["All-rounder"], 2), key=lambda p: p["order"])
    bowl = sorted(random.sample(by_role["Bowler"], 4), key=lambda p: p["order"])
    return bats + wk + ars + bowl


# ------------------------------------------------------------------- seeding
def seed_teams_venues(conn):
    team_ids = {}
    for name, country, short in TEAMS:
        cur = conn.execute("INSERT INTO teams (team_name, country, short_name) VALUES (?,?,?)",
                           (name, country, short))
        team_ids[name] = cur.lastrowid
    venue_ids = {}
    for name, city, country, cap in VENUES:
        cur = conn.execute("INSERT INTO venues (venue_name, city, country, capacity) VALUES (?,?,?,?)",
                           (name, city, country, cap))
        venue_ids[name] = (cur.lastrowid, country)
    return team_ids, venue_ids


def seed_players(conn):
    combos = list(itertools.product(FIRST, LAST))
    random.shuffle(combos)
    names = iter(combos)
    squads = {}
    for team, country, _ in TEAMS:
        squad = []
        for order, role in enumerate(ROLE_PLAN):
            first, last = next(names)
            bat_style = random.choice(BAT_STYLES)
            bowl_style = random.choice(BOWL_STYLES[role])
            dob = date(random.randint(1986, 2004), random.randint(1, 12), random.randint(1, 28))
            cur = conn.execute(
                "INSERT INTO players (full_name, country, playing_role, batting_style, bowling_style, "
                "date_of_birth) VALUES (?,?,?,?,?,?)",
                (f"{first} {last}", country, role, bat_style, bowl_style, dob.isoformat()))
            skill = {"Batsman": (1.0, 1.35), "Wicket-keeper": (0.9, 1.2),
                     "All-rounder": (0.8, 1.15), "Bowler": (0.5, 0.8)}[role]
            squad.append({
                "id": cur.lastrowid, "role": role, "order": order, "country": country,
                "bat_skill": random.uniform(*skill),
                "bowl_skill": random.uniform(0.8, 1.25),
                "slope": random.uniform(-0.12, 0.12),
            })
        squads[team] = squad
    return squads


def seed_career_stats(conn, squads):
    avg_range = {"Batsman": (35, 55), "Wicket-keeper": (30, 45), "All-rounder": (26, 40), "Bowler": (8, 20)}
    for squad in squads.values():
        for p in squad:
            for fmt in FORMATS:
                m = {"Test": random.randint(8, 115), "ODI": random.randint(15, 260),
                     "T20I": random.randint(15, 150)}[fmt]
                innings = max(1, int(m * 0.9))
                avg = round(random.uniform(*avg_range[p["role"]]) * (0.9 if fmt == "T20I" else 1.0), 2)
                runs = int(avg * innings * 0.88)
                hs = min({"Test": 335, "ODI": 264, "T20I": 175}[fmt],
                         max(10, int(avg * random.uniform(3.5, 6.5))))
                sr = round(random.uniform(*{"Test": (45, 62), "ODI": (72, 100), "T20I": (118, 158)}[fmt]), 2)
                hundreds = int(runs / random.uniform(380, 520)) if p["role"] != "Bowler" else 0
                fifties = int(runs / random.uniform(120, 180))
                wickets, bavg, econ = 0, None, None
                if p["role"] in ("Bowler", "All-rounder"):
                    per_match = {"Test": (2.0, 3.8), "ODI": (1.0, 2.0), "T20I": (0.8, 1.5)}[fmt]
                    factor = 1.0 if p["role"] == "Bowler" else 0.6
                    wickets = int(m * random.uniform(*per_match) * factor)
                    bavg = round(random.uniform(22, 32) if p["role"] == "Bowler" else random.uniform(28, 40), 2)
                    econ = round(random.uniform(*{"Test": (2.7, 3.6), "ODI": (4.4, 5.6), "T20I": (6.6, 8.6)}[fmt]), 2)
                catches = int(m * random.uniform(0.2, 0.9))
                stumpings = int(m * random.uniform(0.1, 0.4)) if p["role"] == "Wicket-keeper" else 0
                conn.execute(
                    "INSERT INTO player_career_stats (player_id, match_format, matches, innings, runs, "
                    "highest_score, batting_avg, strike_rate, centuries, fifties, wickets, bowling_avg, "
                    "economy, catches, stumpings) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (p["id"], fmt, m, innings, runs, hs, avg, sr, hundreds, fifties, wickets, bavg,
                     econ, catches, stumpings))


def venue_for(host_country, venue_ids):
    options = [vid for vid, c in venue_ids.values() if c == host_country]
    return random.choice(options)


def insert_innings(conn, match_id, innings_no, team_id, bat, bowl_rows, bowl_team_id):
    conn.execute("INSERT INTO innings (match_id, innings_no, team_id, total_runs, wickets, balls, extras) "
                 "VALUES (?,?,?,?,?,?,?)",
                 (match_id, innings_no, team_id, bat["total"], bat["wickets"], bat["balls"], bat["extras"]))
    for r in bat["rows"]:
        sr = round(r["runs"] * 100 / r["balls"], 2) if r["balls"] else 0.0
        conn.execute(
            "INSERT INTO batting_performances (match_id, innings_no, team_id, player_id, batting_position, "
            "runs, balls_faced, fours, sixes, strike_rate, is_out, out_description) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (match_id, innings_no, team_id, r["player"]["id"], r["pos"], r["runs"], r["balls"], r["fours"],
             r["sixes"], sr, int(r["out"]), r["desc"] if r["out"] else "not out"))
    rows = bat["rows"]
    for k in range(len(rows) - 1):
        a, b = rows[k], rows[k + 1]
        runs = int((a["runs"] + b["runs"]) * random.uniform(0.6, 0.95))
        balls = int((a["balls"] + b["balls"]) * random.uniform(0.6, 0.95))
        conn.execute("INSERT INTO partnerships (match_id, innings_no, wicket_no, batsman1_id, batsman2_id, "
                     "runs, balls) VALUES (?,?,?,?,?,?,?)",
                     (match_id, innings_no, min(k + 1, 10), a["player"]["id"], b["player"]["id"], runs, balls))
    for r in bowl_rows:
        econ = round(r["runs"] / (r["balls"] / 6), 2) if r["balls"] else 0.0
        conn.execute(
            "INSERT INTO bowling_performances (match_id, innings_no, team_id, player_id, balls_bowled, overs, "
            "maidens, runs_conceded, wickets, economy) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (match_id, innings_no, bowl_team_id, r["player"]["id"], r["balls"], overs_notation(r["balls"]),
             r["maidens"], r["runs"], r["wickets"], econ))


def seed_series_and_matches(conn, team_ids, venue_ids, squads):
    team_names = [t[0] for t in TEAMS]
    team_country = {t[0]: t[1] for t in TEAMS}
    span = (TODAY + timedelta(days=10) - START).days
    n_matches = 0

    for _ in range(N_SERIES):
        host = random.choice([t for t in team_names if team_country[t] in HOME_COUNTRIES])
        visitor = random.choice([t for t in team_names if t != host])
        fmt = random.choices(FORMATS, weights=[45, 35, 20])[0]
        count = {"T20I": random.choice([3, 5]), "ODI": random.choice([3, 3, 5]),
                 "Test": random.choice([2, 3, 5])}[fmt]
        start = START + timedelta(days=random.randint(0, span))
        host_country = team_country[host]
        cur = conn.execute(
            "INSERT INTO series (series_name, host_country, match_type, start_date, total_matches) "
            "VALUES (?,?,?,?,?)",
            (f"{visitor} tour of {host_country} {start.year}", host_country, fmt, start.isoformat(), count))
        series_id = cur.lastrowid
        gap = 6 if fmt == "Test" else 3

        for i in range(1, count + 1):
            d = start + timedelta(days=(i - 1) * gap)
            venue_id = venue_for(host_country, venue_ids)
            t1, t2 = host, visitor
            desc = f"{t1} vs {t2}, {ordinal(i)} {fmt}"
            if d > TODAY:
                conn.execute(
                    "INSERT INTO matches (series_id, description, match_format, match_date, venue_id, "
                    "team1_id, team2_id, status) VALUES (?,?,?,?,?,?,?,'Upcoming')",
                    (series_id, desc, fmt, d.isoformat(), venue_id, team_ids[t1], team_ids[t2]))
                continue

            toss_winner = random.choice([t1, t2])
            decision = random.choices(["bat", "bowl"], weights=[40, 60] if fmt != "Test" else [65, 35])[0]
            first = toss_winner if decision == "bat" else (t2 if toss_winner == t1 else t1)
            second = t2 if first == t1 else t1
            xi = {t1: pick_xi(squads[t1]), t2: pick_xi(squads[t2])}
            boost = {t1: 1.05, t2: 1.0}
            winner, margin, vtype = None, None, "draw"

            cur = conn.execute(
                "INSERT INTO matches (series_id, description, match_format, match_date, venue_id, team1_id, "
                "team2_id, toss_winner_id, toss_decision, status) VALUES (?,?,?,?,?,?,?,?,?,'Completed')",
                (series_id, desc, fmt, d.isoformat(), venue_id, team_ids[t1], team_ids[t2],
                 team_ids[toss_winner], decision))
            match_id = cur.lastrowid

            if fmt == "Test":
                order = [first, second, first, second]
                totals = {first: 0, second: 0}
                last = None
                for no, team in enumerate(order, start=1):
                    other = second if team == first else first
                    bat = simulate_batting(xi[team], fmt, d, boost[team], random.randint(350, 620))
                    bowl = simulate_bowling(xi[other], bat, fmt, d)
                    insert_innings(conn, match_id, no, team_ids[team], bat, bowl, team_ids[other])
                    totals[team] += bat["total"]
                    last = bat
                if random.random() >= 0.2:
                    if totals[first] > totals[second]:
                        winner, margin, vtype = first, totals[first] - totals[second], "runs"
                    else:
                        winner, margin, vtype = second, max(2, 10 - last["wickets"]), "wickets"
            else:
                limit = 120 if fmt == "T20I" else 300
                bat1 = simulate_batting(xi[first], fmt, d, boost[first], limit)
                bowl1 = simulate_bowling(xi[second], bat1, fmt, d)
                insert_innings(conn, match_id, 1, team_ids[first], bat1, bowl1, team_ids[second])
                bat2 = simulate_batting(xi[second], fmt, d, boost[second], limit, target=bat1["total"])
                bowl2 = simulate_bowling(xi[first], bat2, fmt, d)
                insert_innings(conn, match_id, 2, team_ids[second], bat2, bowl2, team_ids[first])
                if bat2["total"] > bat1["total"]:
                    winner, margin, vtype = second, 10 - bat2["wickets"], "wickets"
                elif bat2["total"] < bat1["total"]:
                    winner, margin, vtype = first, bat1["total"] - bat2["total"], "runs"
                else:
                    vtype = "tie"

            conn.execute("UPDATE matches SET winner_id=?, victory_margin=?, victory_type=? WHERE match_id=?",
                         (team_ids[winner] if winner else None, margin, vtype, match_id))
            n_matches += 1
    return n_matches


def main() -> None:
    with db_session() as conn:
        if conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] > 0:
            print("Database already has data. Run: python scripts/setup_database.py --reset")
            return
        team_ids, venue_ids = seed_teams_venues(conn)
        squads = seed_players(conn)
        seed_career_stats(conn, squads)
        n = seed_series_and_matches(conn, team_ids, venue_ids, squads)

        print(f"Seeded {n} completed matches (synthetic data).")
        for table in ["teams", "players", "venues", "series", "matches", "innings",
                      "batting_performances", "bowling_performances", "partnerships",
                      "player_career_stats"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:24s}{count}")


if __name__ == "__main__":
    main()
