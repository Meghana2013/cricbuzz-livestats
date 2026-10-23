-- Cricbuzz LiveStats: database schema (SQLite)
-- Run with: python scripts/setup_database.py

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name  TEXT NOT NULL UNIQUE,
    country    TEXT,
    short_name TEXT
);

CREATE TABLE IF NOT EXISTS players (
    player_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    api_player_id INTEGER UNIQUE,              -- Cricbuzz id when loaded from the API
    full_name     TEXT NOT NULL,
    country       TEXT NOT NULL,
    playing_role  TEXT NOT NULL
        CHECK (playing_role IN ('Batsman', 'Bowler', 'All-rounder', 'Wicket-keeper')),
    batting_style TEXT,
    bowling_style TEXT,
    date_of_birth TEXT
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name TEXT NOT NULL,
    city       TEXT NOT NULL,
    country    TEXT NOT NULL,
    capacity   INTEGER CHECK (capacity IS NULL OR capacity > 0),
    UNIQUE (venue_name, city)
);

CREATE TABLE IF NOT EXISTS series (
    series_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name   TEXT NOT NULL,
    host_country  TEXT,
    match_type    TEXT,
    start_date    TEXT,
    total_matches INTEGER
);

CREATE TABLE IF NOT EXISTS matches (
    match_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    api_match_id   INTEGER UNIQUE,
    series_id      INTEGER REFERENCES series (series_id) ON DELETE SET NULL,
    description    TEXT NOT NULL,
    match_format   TEXT,
    match_date     TEXT,
    venue_id       INTEGER REFERENCES venues (venue_id) ON DELETE SET NULL,
    team1_id       INTEGER NOT NULL REFERENCES teams (team_id),
    team2_id       INTEGER NOT NULL REFERENCES teams (team_id),
    toss_winner_id INTEGER REFERENCES teams (team_id),
    toss_decision  TEXT CHECK (toss_decision IN ('bat', 'bowl')),
    winner_id      INTEGER REFERENCES teams (team_id),
    victory_margin INTEGER,
    victory_type   TEXT CHECK (victory_type IN ('runs', 'wickets', 'draw', 'tie', 'no result')),
    status         TEXT NOT NULL DEFAULT 'Completed',
    CHECK (team1_id <> team2_id)
);

CREATE TABLE IF NOT EXISTS innings (
    innings_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id   INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,
    innings_no INTEGER NOT NULL CHECK (innings_no BETWEEN 1 AND 4),
    team_id    INTEGER NOT NULL REFERENCES teams (team_id),
    total_runs INTEGER NOT NULL CHECK (total_runs >= 0),
    wickets    INTEGER NOT NULL CHECK (wickets BETWEEN 0 AND 10),
    balls      INTEGER NOT NULL CHECK (balls >= 0),
    extras     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (match_id, innings_no)
);

CREATE TABLE IF NOT EXISTS batting_performances (
    batting_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,
    innings_no       INTEGER NOT NULL,
    team_id          INTEGER NOT NULL REFERENCES teams (team_id),
    player_id        INTEGER NOT NULL REFERENCES players (player_id) ON DELETE CASCADE,
    batting_position INTEGER NOT NULL CHECK (batting_position BETWEEN 1 AND 11),
    runs             INTEGER NOT NULL CHECK (runs >= 0),
    balls_faced      INTEGER NOT NULL CHECK (balls_faced >= 0),
    fours            INTEGER NOT NULL DEFAULT 0,
    sixes            INTEGER NOT NULL DEFAULT 0,
    strike_rate      REAL,
    is_out           INTEGER NOT NULL DEFAULT 1 CHECK (is_out IN (0, 1)),
    out_description  TEXT,
    UNIQUE (match_id, innings_no, player_id)
);

CREATE TABLE IF NOT EXISTS bowling_performances (
    bowling_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id       INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,
    innings_no     INTEGER NOT NULL,
    team_id        INTEGER NOT NULL REFERENCES teams (team_id),
    player_id      INTEGER NOT NULL REFERENCES players (player_id) ON DELETE CASCADE,
    balls_bowled   INTEGER NOT NULL CHECK (balls_bowled >= 0),
    overs          REAL NOT NULL,              -- cricket notation, e.g. 3.4
    maidens        INTEGER NOT NULL DEFAULT 0,
    runs_conceded  INTEGER NOT NULL CHECK (runs_conceded >= 0),
    wickets        INTEGER NOT NULL DEFAULT 0 CHECK (wickets BETWEEN 0 AND 10),
    economy        REAL,
    UNIQUE (match_id, innings_no, player_id)
);

CREATE TABLE IF NOT EXISTS partnerships (
    partnership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id       INTEGER NOT NULL REFERENCES matches (match_id) ON DELETE CASCADE,
    innings_no     INTEGER NOT NULL,
    wicket_no      INTEGER NOT NULL CHECK (wicket_no BETWEEN 1 AND 10),
    batsman1_id    INTEGER NOT NULL REFERENCES players (player_id) ON DELETE CASCADE,
    batsman2_id    INTEGER NOT NULL REFERENCES players (player_id) ON DELETE CASCADE,
    runs           INTEGER NOT NULL CHECK (runs >= 0),
    balls          INTEGER NOT NULL CHECK (balls >= 0)
);

CREATE TABLE IF NOT EXISTS player_career_stats (
    player_id     INTEGER NOT NULL REFERENCES players (player_id) ON DELETE CASCADE,
    match_format  TEXT NOT NULL CHECK (match_format IN ('Test', 'ODI', 'T20I')),
    matches       INTEGER NOT NULL DEFAULT 0,
    innings       INTEGER NOT NULL DEFAULT 0,
    runs          INTEGER NOT NULL DEFAULT 0,
    highest_score INTEGER NOT NULL DEFAULT 0,
    batting_avg   REAL,
    strike_rate   REAL,
    centuries     INTEGER NOT NULL DEFAULT 0,
    fifties       INTEGER NOT NULL DEFAULT 0,
    wickets       INTEGER NOT NULL DEFAULT 0,
    bowling_avg   REAL,
    economy       REAL,
    catches       INTEGER NOT NULL DEFAULT 0,
    stumpings     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, match_format)
);

-- Indexes for columns used in joins, filters and sorting
CREATE INDEX IF NOT EXISTS idx_players_country    ON players (country);
CREATE INDEX IF NOT EXISTS idx_players_role       ON players (playing_role);
CREATE INDEX IF NOT EXISTS idx_venues_country     ON venues (country);
CREATE INDEX IF NOT EXISTS idx_series_start       ON series (start_date);
CREATE INDEX IF NOT EXISTS idx_matches_date       ON matches (match_date);
CREATE INDEX IF NOT EXISTS idx_matches_venue      ON matches (venue_id);
CREATE INDEX IF NOT EXISTS idx_matches_winner     ON matches (winner_id);
CREATE INDEX IF NOT EXISTS idx_matches_format     ON matches (match_format);
CREATE INDEX IF NOT EXISTS idx_batting_player     ON batting_performances (player_id);
CREATE INDEX IF NOT EXISTS idx_batting_match      ON batting_performances (match_id);
CREATE INDEX IF NOT EXISTS idx_bowling_player     ON bowling_performances (player_id);
CREATE INDEX IF NOT EXISTS idx_bowling_match      ON bowling_performances (match_id);
CREATE INDEX IF NOT EXISTS idx_partnership_match  ON partnerships (match_id, innings_no);

-- Views: saved queries reused by several pages
CREATE VIEW IF NOT EXISTS v_match_results AS
SELECT m.match_id,
       m.description,
       m.match_format,
       m.match_date,
       m.status,
       t1.team_name AS team1,
       t2.team_name AS team2,
       w.team_name  AS winner,
       m.victory_margin,
       m.victory_type,
       v.venue_name,
       v.city,
       v.country    AS venue_country
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
LEFT JOIN teams w  ON w.team_id = m.winner_id
LEFT JOIN venues v ON v.venue_id = m.venue_id;

CREATE VIEW IF NOT EXISTS v_batting_detail AS
SELECT b.*,
       p.full_name,
       m.match_date,
       m.match_format
FROM batting_performances b
JOIN players p ON p.player_id = b.player_id
JOIN matches m ON m.match_id  = b.match_id;
