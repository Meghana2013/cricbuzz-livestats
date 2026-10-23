"""Business logic for player CRUD: validation + SQL. Used by the CRUD page."""
from datetime import date
from typing import Optional

import pandas as pd

from utils.db_connection import db_session, fetch_df

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]
BATTING_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWLING_STYLES = ["Right-arm fast", "Left-arm fast", "Right-arm medium", "Right-arm offbreak",
                  "Legbreak", "Left-arm orthodox"]
FORMATS = ["Test", "ODI", "T20I"]
_UPDATABLE = {"full_name", "country", "playing_role", "batting_style", "bowling_style", "date_of_birth"}


class ValidationError(ValueError):
    """Raised when user input is invalid (message is safe to show on screen)."""


def validate_player(full_name: str, country: str, playing_role: str,
                    date_of_birth: Optional[date] = None) -> list:
    """Return a list of human-readable problems (empty list means valid)."""
    errors = []
    if not full_name or len(full_name.strip()) < 3:
        errors.append("Full name must have at least 3 characters.")
    if not country or not country.strip():
        errors.append("Country is required.")
    if playing_role not in ROLES:
        errors.append(f"Playing role must be one of: {', '.join(ROLES)}.")
    if date_of_birth is not None:
        if date_of_birth > date.today():
            errors.append("Date of birth cannot be in the future.")
        elif date_of_birth.year < 1940:
            errors.append("Date of birth looks too old (before 1940).")
    return errors


def list_players(search: str = "", country: str = "", role: str = "") -> pd.DataFrame:
    """Return players, optionally filtered by name text, country and role."""
    sql = ("SELECT player_id, full_name, country, playing_role, batting_style, bowling_style, "
           "date_of_birth FROM players WHERE 1=1")
    params = []
    if search:
        sql += " AND full_name LIKE ?"
        params.append(f"%{search.strip()}%")
    if country:
        sql += " AND country = ?"
        params.append(country)
    if role:
        sql += " AND playing_role = ?"
        params.append(role)
    return fetch_df(sql + " ORDER BY full_name", params)


def list_countries() -> list:
    return fetch_df("SELECT DISTINCT country FROM players ORDER BY country")["country"].tolist()


def get_player(player_id: int) -> Optional[dict]:
    df = fetch_df("SELECT * FROM players WHERE player_id = ?", [player_id])
    return None if df.empty else df.iloc[0].to_dict()


def create_player(full_name: str, country: str, playing_role: str,
                  batting_style: Optional[str] = None, bowling_style: Optional[str] = None,
                  date_of_birth: Optional[date] = None) -> int:
    """Insert a player and return the new player_id."""
    errors = validate_player(full_name, country, playing_role, date_of_birth)
    if errors:
        raise ValidationError(" ".join(errors))
    dob = date_of_birth.isoformat() if date_of_birth else None
    with db_session() as conn:
        duplicate = conn.execute(
            "SELECT 1 FROM players WHERE lower(full_name) = lower(?) AND country = ? "
            "AND COALESCE(date_of_birth, '') = COALESCE(?, '')",
            (full_name.strip(), country.strip(), dob)).fetchone()
        if duplicate:
            raise ValidationError("A player with the same name, country and date of birth already exists.")
        cur = conn.execute(
            "INSERT INTO players (full_name, country, playing_role, batting_style, bowling_style, "
            "date_of_birth) VALUES (?,?,?,?,?,?)",
            (full_name.strip(), country.strip(), playing_role, batting_style, bowling_style, dob))
        return cur.lastrowid


def update_player(player_id: int, **fields) -> None:
    """Update the given fields of a player."""
    unknown = set(fields) - _UPDATABLE
    if unknown:
        raise ValidationError(f"Cannot update: {', '.join(sorted(unknown))}")
    current = get_player(player_id)
    if current is None:
        raise ValidationError("Player not found.")
    merged = {**current, **fields}
    dob = merged.get("date_of_birth")
    dob_date = date.fromisoformat(dob) if isinstance(dob, str) and dob else (dob if isinstance(dob, date) else None)
    errors = validate_player(merged["full_name"], merged["country"], merged["playing_role"], dob_date)
    if errors:
        raise ValidationError(" ".join(errors))
    if isinstance(fields.get("date_of_birth"), date):
        fields["date_of_birth"] = fields["date_of_birth"].isoformat()
    assignments = ", ".join(f"{col} = ?" for col in fields)
    with db_session() as conn:
        conn.execute(f"UPDATE players SET {assignments} WHERE player_id = ?",
                     [*fields.values(), player_id])


def player_usage(player_id: int) -> dict:
    """How many linked rows would be removed together with this player."""
    queries = {
        "batting rows": "SELECT COUNT(*) FROM batting_performances WHERE player_id = ?",
        "bowling rows": "SELECT COUNT(*) FROM bowling_performances WHERE player_id = ?",
        "partnerships": "SELECT COUNT(*) FROM partnerships WHERE batsman1_id = ? OR batsman2_id = ?",
        "career stat rows": "SELECT COUNT(*) FROM player_career_stats WHERE player_id = ?",
    }
    result = {}
    with db_session() as conn:
        for label, sql in queries.items():
            n_params = sql.count("?")
            result[label] = conn.execute(sql, [player_id] * n_params).fetchone()[0]
    return result


def delete_player(player_id: int) -> None:
    """Delete a player (linked performance rows are removed by ON DELETE CASCADE)."""
    with db_session() as conn:
        cur = conn.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
        if cur.rowcount == 0:
            raise ValidationError("Player not found.")


def get_career_stats(player_id: int) -> pd.DataFrame:
    return fetch_df("SELECT match_format, matches, innings, runs, highest_score, batting_avg, "
                    "strike_rate, centuries, fifties, wickets, catches FROM player_career_stats "
                    "WHERE player_id = ? ORDER BY match_format", [player_id])


def upsert_career_stats(player_id: int, match_format: str, matches: int, innings: int, runs: int,
                        highest_score: int, batting_avg: float, strike_rate: float,
                        centuries: int, fifties: int, wickets: int, catches: int) -> None:
    """Insert or update one player's career row for one format."""
    if match_format not in FORMATS:
        raise ValidationError("Format must be Test, ODI or T20I.")
    ints = {"matches": matches, "innings": innings, "runs": runs, "highest_score": highest_score,
            "centuries": centuries, "fifties": fifties, "wickets": wickets, "catches": catches}
    bad = [k for k, v in ints.items() if v < 0]
    if bad or batting_avg < 0 or strike_rate < 0:
        raise ValidationError("Statistics cannot be negative.")
    if innings > matches:
        raise ValidationError("Innings cannot be more than matches.")
    if highest_score > runs:
        raise ValidationError("Highest score cannot be more than total runs.")
    if get_player(player_id) is None:
        raise ValidationError("Player not found.")
    with db_session() as conn:
        conn.execute(
            "INSERT INTO player_career_stats (player_id, match_format, matches, innings, runs, "
            "highest_score, batting_avg, strike_rate, centuries, fifties, wickets, catches) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(player_id, match_format) DO UPDATE SET matches=excluded.matches, "
            "innings=excluded.innings, runs=excluded.runs, highest_score=excluded.highest_score, "
            "batting_avg=excluded.batting_avg, strike_rate=excluded.strike_rate, "
            "centuries=excluded.centuries, fifties=excluded.fifties, wickets=excluded.wickets, "
            "catches=excluded.catches",
            (player_id, match_format, matches, innings, runs, highest_score, batting_avg,
             strike_rate, centuries, fifties, wickets, catches))
