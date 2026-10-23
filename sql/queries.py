"""The 25 SQL analytics questions for the Cricbuzz LiveStats project.

Each entry: id, level, title, question, sql.
The Streamlit "SQL Analytics" page loops over QUERIES, so adding a query here
adds it to the page automatically.
"""

QUERIES = [
    # ------------------------------------------------------------ BEGINNER
    {
        "id": 1, "level": "Beginner",
        "title": "Players who represent India",
        "question": "Find all players who represent India: full name, playing role, batting style, bowling style.",
        "sql": """
SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
ORDER BY full_name;
""",
    },
    {
        "id": 2, "level": "Beginner",
        "title": "Matches in the last 30 days",
        "question": "Matches played in the last 30 days with description, both teams, venue with city and date, newest first.",
        "sql": """
SELECT m.description,
       t1.team_name AS team1,
       t2.team_name AS team2,
       v.venue_name || ', ' || v.city AS venue,
       m.match_date
FROM matches m
JOIN teams t1 ON t1.team_id = m.team1_id
JOIN teams t2 ON t2.team_id = m.team2_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.status = 'Completed'
  AND m.match_date BETWEEN date('now', '-30 day') AND date('now')
ORDER BY m.match_date DESC, m.match_id DESC;
""",
    },
    {
        "id": 3, "level": "Beginner",
        "title": "Top 10 ODI run scorers",
        "question": "Top 10 highest run scorers in ODI cricket: name, total runs, batting average, centuries.",
        "sql": """
SELECT p.full_name,
       s.runs AS total_runs,
       s.batting_avg,
       s.centuries
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
WHERE s.match_format = 'ODI'
ORDER BY s.runs DESC
LIMIT 10;
""",
    },
    {
        "id": 4, "level": "Beginner",
        "title": "Venues with capacity above 50,000",
        "question": "Venues with a seating capacity of more than 50,000: name, city, country, capacity, largest first.",
        "sql": """
SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;
""",
    },
    {
        "id": 5, "level": "Beginner",
        "title": "Wins per team",
        "question": "How many matches has each team won? Most wins first.",
        "sql": """
SELECT t.team_name,
       COUNT(m.match_id) AS total_wins
FROM teams t
LEFT JOIN matches m ON m.winner_id = t.team_id
GROUP BY t.team_id, t.team_name
ORDER BY total_wins DESC, t.team_name;
""",
    },
    {
        "id": 6, "level": "Beginner",
        "title": "Players per role",
        "question": "Count how many players belong to each playing role.",
        "sql": """
SELECT playing_role,
       COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC;
""",
    },
    {
        "id": 7, "level": "Beginner",
        "title": "Highest individual score per format",
        "question": "Highest individual batting score achieved in each format (Test, ODI, T20I).",
        "sql": """
SELECT match_format AS format,
       MAX(highest_score) AS highest_score
FROM player_career_stats
GROUP BY match_format
ORDER BY highest_score DESC;
""",
    },
    {
        "id": 8, "level": "Beginner",
        "title": "Series that started in 2024",
        "question": "Series that started in 2024: name, host country, match type, start date, planned matches.",
        "sql": """
SELECT series_name, host_country, match_type, start_date, total_matches
FROM series
WHERE strftime('%Y', start_date) = '2024'
ORDER BY start_date;
""",
    },
    # -------------------------------------------------------- INTERMEDIATE
    {
        "id": 9, "level": "Intermediate",
        "title": "All-rounders with 1000+ runs and 50+ wickets",
        "question": "All-rounders with more than 1000 runs AND more than 50 wickets: name, runs, wickets, format.",
        "sql": """
SELECT p.full_name,
       s.runs AS total_runs,
       s.wickets AS total_wickets,
       s.match_format AS format
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
WHERE p.playing_role = 'All-rounder'
  AND s.runs > 1000
  AND s.wickets > 50
ORDER BY s.runs DESC;
""",
    },
    {
        "id": 10, "level": "Intermediate",
        "title": "Last 20 completed matches",
        "question": "Details of the last 20 completed matches: teams, winner, margin, victory type, venue.",
        "sql": """
SELECT description,
       team1,
       team2,
       COALESCE(winner, victory_type) AS winning_team,
       victory_margin,
       victory_type,
       venue_name,
       match_date
FROM v_match_results
WHERE status = 'Completed'
ORDER BY match_date DESC, match_id DESC
LIMIT 20;
""",
    },
    {
        "id": 11, "level": "Intermediate",
        "title": "Player performance across formats",
        "question": "For players who played at least 2 formats: runs in Test, ODI, T20I and overall batting average.",
        "sql": """
SELECT p.full_name,
       SUM(CASE WHEN s.match_format = 'Test' THEN s.runs END) AS test_runs,
       SUM(CASE WHEN s.match_format = 'ODI'  THEN s.runs END) AS odi_runs,
       SUM(CASE WHEN s.match_format = 'T20I' THEN s.runs END) AS t20i_runs,
       ROUND(SUM(s.batting_avg * s.innings) / SUM(s.innings), 2) AS overall_batting_avg
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
WHERE s.matches > 0
GROUP BY s.player_id, p.full_name
HAVING COUNT(DISTINCT s.match_format) >= 2
ORDER BY overall_batting_avg DESC;
""",
    },
    {
        "id": 12, "level": "Intermediate",
        "title": "Home vs away wins",
        "question": "Each team's wins at home (venue country = team country) versus away.",
        "sql": """
SELECT t.team_name,
       SUM(CASE WHEN v.country = t.country THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN v.country <> t.country THEN 1 ELSE 0 END) AS away_wins
FROM teams t
LEFT JOIN matches m ON m.winner_id = t.team_id
LEFT JOIN venues v ON v.venue_id = m.venue_id
GROUP BY t.team_id, t.team_name
ORDER BY home_wins + away_wins DESC;
""",
    },
    {
        "id": 13, "level": "Intermediate",
        "title": "Partnerships of 100+ between consecutive batsmen",
        "question": "Partnerships of 100+ runs between batsmen in adjacent batting positions, with the innings.",
        "sql": """
SELECT p1.full_name AS player1,
       p2.full_name AS player2,
       pt.runs AS partnership_runs,
       m.description || ' (innings ' || pt.innings_no || ')' AS innings,
       m.match_date
FROM partnerships pt
JOIN batting_performances b1 ON b1.match_id = pt.match_id
                            AND b1.innings_no = pt.innings_no
                            AND b1.player_id = pt.batsman1_id
JOIN batting_performances b2 ON b2.match_id = pt.match_id
                            AND b2.innings_no = pt.innings_no
                            AND b2.player_id = pt.batsman2_id
JOIN players p1 ON p1.player_id = pt.batsman1_id
JOIN players p2 ON p2.player_id = pt.batsman2_id
JOIN matches m  ON m.match_id = pt.match_id
WHERE ABS(b1.batting_position - b2.batting_position) = 1
  AND pt.runs >= 100
ORDER BY pt.runs DESC;
""",
    },
    {
        "id": 14, "level": "Intermediate",
        "title": "Bowling performance by venue",
        "question": "Bowlers with 3+ matches at the same venue (4+ overs each match): average economy, wickets, matches.",
        "sql": """
WITH per_match AS (
    SELECT bp.player_id, bp.match_id, m.venue_id,
           SUM(bp.balls_bowled)  AS balls,
           SUM(bp.runs_conceded) AS runs,
           SUM(bp.wickets)       AS wkts
    FROM bowling_performances bp
    JOIN matches m ON m.match_id = bp.match_id
    GROUP BY bp.player_id, bp.match_id
)
SELECT p.full_name,
       v.venue_name,
       COUNT(*) AS matches_played,
       ROUND(SUM(pm.runs) * 6.0 / SUM(pm.balls), 2) AS avg_economy,
       SUM(pm.wkts) AS total_wickets
FROM per_match pm
JOIN players p ON p.player_id = pm.player_id
JOIN venues v  ON v.venue_id  = pm.venue_id
WHERE pm.balls >= 24
GROUP BY pm.player_id, pm.venue_id
HAVING COUNT(*) >= 3
ORDER BY avg_economy ASC;
""",
    },
    {
        "id": 15, "level": "Intermediate",
        "title": "Players in close matches",
        "question": "Close matches (won by under 50 runs or under 5 wickets): average runs, matches played, matches won.",
        "sql": """
WITH close_matches AS (
    SELECT match_id, winner_id
    FROM matches
    WHERE status = 'Completed'
      AND ((victory_type = 'runs'    AND victory_margin < 50)
        OR (victory_type = 'wickets' AND victory_margin < 5))
),
per_player AS (
    SELECT b.player_id, b.match_id, b.team_id, SUM(b.runs) AS runs
    FROM batting_performances b
    JOIN close_matches c ON c.match_id = b.match_id
    GROUP BY b.player_id, b.match_id, b.team_id
)
SELECT p.full_name,
       ROUND(AVG(pp.runs), 2) AS avg_runs,
       COUNT(*) AS close_matches_played,
       SUM(CASE WHEN pp.team_id = c.winner_id THEN 1 ELSE 0 END) AS close_matches_won
FROM per_player pp
JOIN close_matches c ON c.match_id = pp.match_id
JOIN players p ON p.player_id = pp.player_id
GROUP BY pp.player_id, p.full_name
HAVING COUNT(*) >= 5
ORDER BY avg_runs DESC;
""",
    },
    {
        "id": 16, "level": "Intermediate",
        "title": "Batting performance by year since 2020",
        "question": "Per year since 2020: each player's average runs per match and average strike rate (5+ matches that year).",
        "sql": """
SELECT full_name,
       strftime('%Y', match_date) AS year,
       COUNT(DISTINCT match_id) AS matches,
       ROUND(SUM(runs) * 1.0 / COUNT(DISTINCT match_id), 2) AS avg_runs_per_match,
       ROUND(AVG(strike_rate), 2) AS avg_strike_rate
FROM v_batting_detail
WHERE match_date >= '2020-01-01'
GROUP BY player_id, full_name, year
HAVING COUNT(DISTINCT match_id) >= 5
ORDER BY year, avg_runs_per_match DESC;
""",
    },
    # ------------------------------------------------------------ ADVANCED
    {
        "id": 17, "level": "Advanced",
        "title": "Does winning the toss help?",
        "question": "Percentage of matches won by the toss winner, split by toss decision (bat or bowl first).",
        "sql": """
SELECT toss_decision,
       COUNT(*) AS matches,
       SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) AS toss_winner_won,
       ROUND(100.0 * SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM matches
WHERE status = 'Completed' AND winner_id IS NOT NULL AND toss_decision IS NOT NULL
GROUP BY toss_decision
UNION ALL
SELECT 'overall',
       COUNT(*),
       SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM matches
WHERE status = 'Completed' AND winner_id IS NOT NULL AND toss_decision IS NOT NULL;
""",
    },
    {
        "id": 18, "level": "Advanced",
        "title": "Most economical bowlers in limited overs",
        "question": "Most economical bowlers in ODI and T20I (10+ matches, at least 2 overs per match on average).",
        "sql": """
WITH per_match AS (
    SELECT bp.player_id, bp.match_id,
           SUM(bp.balls_bowled)  AS balls,
           SUM(bp.runs_conceded) AS runs,
           SUM(bp.wickets)       AS wkts
    FROM bowling_performances bp
    JOIN matches m ON m.match_id = bp.match_id
    WHERE m.match_format IN ('ODI', 'T20I')
    GROUP BY bp.player_id, bp.match_id
)
SELECT p.full_name,
       COUNT(*) AS matches,
       ROUND(SUM(pm.balls) / 6.0 / COUNT(*), 2) AS avg_overs_per_match,
       ROUND(SUM(pm.runs) * 6.0 / SUM(pm.balls), 2) AS economy_rate,
       SUM(pm.wkts) AS total_wickets
FROM per_match pm
JOIN players p ON p.player_id = pm.player_id
GROUP BY pm.player_id, p.full_name
HAVING COUNT(*) >= 10 AND SUM(pm.balls) / 6.0 / COUNT(*) >= 2
ORDER BY economy_rate ASC
LIMIT 25;
""",
    },
    {
        "id": 19, "level": "Advanced",
        "title": "Most consistent batsmen",
        "question": "Average runs and standard deviation per player since 2022 (innings of 10+ balls). Lower deviation = more consistent.",
        "sql": """
SELECT full_name,
       COUNT(*) AS innings,
       ROUND(AVG(runs), 2) AS avg_runs,
       ROUND(STDDEV(runs), 2) AS std_dev
FROM v_batting_detail
WHERE match_date >= '2022-01-01'
  AND balls_faced >= 10
GROUP BY player_id, full_name
HAVING COUNT(*) >= 10
ORDER BY std_dev ASC
LIMIT 25;
""",
    },
    {
        "id": 20, "level": "Advanced",
        "title": "Matches and batting average by format",
        "question": "Test/ODI/T20 match counts and batting averages for players with 20+ total matches.",
        "sql": """
SELECT p.full_name,
       SUM(CASE WHEN s.match_format = 'Test' THEN s.matches END) AS test_matches,
       SUM(CASE WHEN s.match_format = 'ODI'  THEN s.matches END) AS odi_matches,
       SUM(CASE WHEN s.match_format = 'T20I' THEN s.matches END) AS t20i_matches,
       MAX(CASE WHEN s.match_format = 'Test' THEN s.batting_avg END) AS test_avg,
       MAX(CASE WHEN s.match_format = 'ODI'  THEN s.batting_avg END) AS odi_avg,
       MAX(CASE WHEN s.match_format = 'T20I' THEN s.batting_avg END) AS t20i_avg
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
GROUP BY s.player_id, p.full_name
HAVING SUM(s.matches) >= 20
ORDER BY SUM(s.matches) DESC;
""",
    },
    {
        "id": 21, "level": "Advanced",
        "title": "Weighted performance ranking",
        "question": "Combine batting, bowling and fielding into one weighted score and rank the top 10 per format.",
        "sql": """
WITH scored AS (
    SELECT p.full_name,
           s.match_format AS format,
           s.runs * 0.01 + COALESCE(s.batting_avg, 0) * 0.5 + COALESCE(s.strike_rate, 0) * 0.3 AS batting_pts,
           CASE WHEN s.bowling_avg IS NULL THEN 0
                ELSE s.wickets * 2 + (50 - s.bowling_avg) * 0.5 + (6 - s.economy) * 2
           END AS bowling_pts,
           s.catches * 3 + s.stumpings * 5 AS fielding_pts
    FROM player_career_stats s
    JOIN players p ON p.player_id = s.player_id
),
ranked AS (
    SELECT *,
           batting_pts + bowling_pts + fielding_pts AS total_pts,
           RANK() OVER (PARTITION BY format
                        ORDER BY batting_pts + bowling_pts + fielding_pts DESC) AS rank_in_format
    FROM scored
)
SELECT format, rank_in_format, full_name,
       ROUND(batting_pts, 1) AS batting_pts,
       ROUND(bowling_pts, 1) AS bowling_pts,
       ROUND(fielding_pts, 1) AS fielding_pts,
       ROUND(total_pts, 1) AS total_pts
FROM ranked
WHERE rank_in_format <= 10
ORDER BY format, rank_in_format;
""",
    },
    {
        "id": 22, "level": "Advanced",
        "title": "Head-to-head analysis (last 3 years)",
        "question": "Team pairs with 5+ matches in the last 3 years: wins, average run margin, win %, wins when batting first.",
        "sql": """
WITH recent AS (
    SELECT m.*,
           MIN(team1_id, team2_id) AS ta,
           MAX(team1_id, team2_id) AS tb,
           CASE WHEN toss_decision = 'bat' THEN toss_winner_id
                WHEN toss_winner_id = team1_id THEN team2_id
                ELSE team1_id END AS bat_first_id
    FROM matches m
    WHERE status = 'Completed' AND match_date >= date('now', '-3 years')
)
SELECT a.team_name AS team_a,
       b.team_name AS team_b,
       COUNT(*) AS matches,
       SUM(CASE WHEN r.winner_id = r.ta THEN 1 ELSE 0 END) AS team_a_wins,
       SUM(CASE WHEN r.winner_id = r.tb THEN 1 ELSE 0 END) AS team_b_wins,
       ROUND(AVG(CASE WHEN r.winner_id = r.ta AND r.victory_type = 'runs' THEN r.victory_margin END), 1) AS a_avg_run_margin,
       ROUND(AVG(CASE WHEN r.winner_id = r.tb AND r.victory_type = 'runs' THEN r.victory_margin END), 1) AS b_avg_run_margin,
       ROUND(100.0 * SUM(CASE WHEN r.winner_id = r.ta THEN 1 ELSE 0 END) / COUNT(*), 1) AS team_a_win_pct,
       ROUND(100.0 * SUM(CASE WHEN r.winner_id = r.tb THEN 1 ELSE 0 END) / COUNT(*), 1) AS team_b_win_pct,
       SUM(CASE WHEN r.winner_id = r.bat_first_id THEN 1 ELSE 0 END) AS wins_batting_first,
       SUM(CASE WHEN r.winner_id IS NOT NULL AND r.winner_id <> r.bat_first_id THEN 1 ELSE 0 END) AS wins_bowling_first
FROM recent r
JOIN teams a ON a.team_id = r.ta
JOIN teams b ON b.team_id = r.tb
GROUP BY r.ta, r.tb
HAVING COUNT(*) >= 5
ORDER BY matches DESC;
""",
    },
    {
        "id": 23, "level": "Advanced",
        "title": "Recent player form",
        "question": "Last 10 batting performances: average of last 5 vs last 10, strike rate trend, 50+ scores, consistency, form category.",
        "sql": """
WITH ranked AS (
    SELECT player_id, full_name, runs, strike_rate,
           ROW_NUMBER() OVER (PARTITION BY player_id
                              ORDER BY match_date DESC, batting_id DESC) AS rn
    FROM v_batting_detail
),
agg AS (
    SELECT player_id, full_name,
           AVG(CASE WHEN rn <= 5 THEN runs END) AS avg_last5,
           AVG(runs) AS avg_last10,
           AVG(CASE WHEN rn <= 5 THEN strike_rate END) AS sr_last5,
           AVG(CASE WHEN rn > 5  THEN strike_rate END) AS sr_prev5,
           SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS scores_50_plus,
           STDDEV(runs) AS std_dev
    FROM ranked
    WHERE rn <= 10
    GROUP BY player_id, full_name
    HAVING COUNT(*) = 10
)
SELECT full_name,
       ROUND(avg_last5, 1)  AS avg_last_5,
       ROUND(avg_last10, 1) AS avg_last_10,
       ROUND(sr_last5 - sr_prev5, 1) AS strike_rate_trend,
       scores_50_plus,
       ROUND(100 * MAX(0, 1 - COALESCE(std_dev / NULLIF(avg_last10, 0), 1)), 1) AS consistency_score,
       CASE WHEN avg_last5 >= 30 AND avg_last10 >= 25 THEN 'Excellent Form'
            WHEN avg_last10 >= 20 THEN 'Good Form'
            WHEN avg_last10 >= 12 THEN 'Average Form'
            ELSE 'Poor Form' END AS form_category
FROM agg
ORDER BY avg_last5 DESC;
""",
    },
    {
        "id": 24, "level": "Advanced",
        "title": "Best batting partnerships",
        "question": "Consecutive-position pairs with 5+ partnerships: average runs, 50+ count, best, success rate; ranked.",
        "sql": """
WITH consecutive AS (
    SELECT MIN(pt.batsman1_id, pt.batsman2_id) AS a,
           MAX(pt.batsman1_id, pt.batsman2_id) AS b,
           pt.runs
    FROM partnerships pt
    JOIN batting_performances b1 ON b1.match_id = pt.match_id
                                AND b1.innings_no = pt.innings_no
                                AND b1.player_id = pt.batsman1_id
    JOIN batting_performances b2 ON b2.match_id = pt.match_id
                                AND b2.innings_no = pt.innings_no
                                AND b2.player_id = pt.batsman2_id
    WHERE ABS(b1.batting_position - b2.batting_position) = 1
),
pairs AS (
    SELECT a, b,
           COUNT(*) AS partnerships,
           ROUND(AVG(runs), 1) AS avg_runs,
           SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) AS over_50,
           MAX(runs) AS highest,
           ROUND(100.0 * SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_rate
    FROM consecutive
    GROUP BY a, b
    HAVING COUNT(*) >= 5
)
SELECT RANK() OVER (ORDER BY success_rate DESC, avg_runs DESC) AS rank,
       pa.full_name AS player1,
       pb.full_name AS player2,
       partnerships, avg_runs, over_50, highest, success_rate
FROM pairs
JOIN players pa ON pa.player_id = pairs.a
JOIN players pb ON pb.player_id = pairs.b
ORDER BY rank
LIMIT 25;
""",
    },
    {
        "id": 25, "level": "Advanced",
        "title": "Career trajectory (quarterly time series)",
        "question": "Quarterly averages per player (3+ matches per quarter, 6+ quarters), compared over time to label the career phase.",
        "sql": """
WITH quarterly AS (
    SELECT player_id, full_name,
           strftime('%Y', match_date) || '-Q' ||
               ((CAST(strftime('%m', match_date) AS INTEGER) + 2) / 3) AS quarter,
           COUNT(DISTINCT match_id) AS matches,
           AVG(runs) AS avg_runs,
           AVG(strike_rate) AS avg_sr
    FROM v_batting_detail
    GROUP BY player_id, full_name, quarter
    HAVING COUNT(DISTINCT match_id) >= 3
),
eligible AS (
    SELECT player_id FROM quarterly GROUP BY player_id HAVING COUNT(*) >= 6
),
ordered AS (
    SELECT q.*,
           ROW_NUMBER() OVER (PARTITION BY q.player_id ORDER BY q.quarter) AS rn,
           COUNT(*)     OVER (PARTITION BY q.player_id) AS total_q
    FROM quarterly q
    WHERE q.player_id IN (SELECT player_id FROM eligible)
),
summary AS (
    SELECT player_id, full_name,
           MAX(total_q) AS quarters,
           AVG(CASE WHEN rn <= 3 THEN avg_runs END) AS early_avg,
           AVG(CASE WHEN rn > total_q - 3 THEN avg_runs END) AS recent_avg,
           AVG(CASE WHEN rn <= 3 THEN avg_sr END) AS early_sr,
           AVG(CASE WHEN rn > total_q - 3 THEN avg_sr END) AS recent_sr
    FROM ordered
    GROUP BY player_id, full_name
)
SELECT full_name,
       quarters,
       ROUND(early_avg, 1)  AS early_avg_runs,
       ROUND(recent_avg, 1) AS recent_avg_runs,
       ROUND(early_sr, 1)   AS early_strike_rate,
       ROUND(recent_sr, 1)  AS recent_strike_rate,
       CASE WHEN recent_avg > early_avg * 1.10 THEN 'Career Ascending'
            WHEN recent_avg < early_avg * 0.90 THEN 'Career Declining'
            ELSE 'Career Stable' END AS career_phase
FROM summary
ORDER BY recent_avg - early_avg DESC;
""",
    },
]


def get_query(query_id: int) -> dict:
    """Return the query dict with the given id, or raise KeyError."""
    for q in QUERIES:
        if q["id"] == query_id:
            return q
    raise KeyError(f"No query with id {query_id}")
