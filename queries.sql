-- Premier League Analysis - SQL queries
-- Data: football-data.co.uk E0.csv files, seasons 2023/24 and 2024/25
--
-- How to load the data:
--   Run analysis.py first. It cleans the two season CSVs and loads them
--   into premier_league.db as a table called "matches" with columns:
--   Season, Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR, TotalGoals
--   (FTHG/FTAG = full-time home/away goals, FTR = H/D/A result)
-- Then run any query below with:  sqlite3 premier_league.db < queries.sql

-- Q1. Top 5 attacks across both seasons combined (total goals scored)
SELECT team, SUM(gf) AS goals_scored
FROM (
    SELECT HomeTeam AS team, FTHG AS gf FROM matches
    UNION ALL
    SELECT AwayTeam AS team, FTAG AS gf FROM matches
)
GROUP BY team
ORDER BY goals_scored DESC
LIMIT 5;

-- Q2. Liverpool's home record by season (played, won, drawn, lost, GF, GA)
SELECT Season,
       COUNT(*)                                       AS played,
       SUM(CASE WHEN FTR = 'H' THEN 1 ELSE 0 END)     AS won,
       SUM(CASE WHEN FTR = 'D' THEN 1 ELSE 0 END)     AS drawn,
       SUM(CASE WHEN FTR = 'A' THEN 1 ELSE 0 END)     AS lost,
       SUM(FTHG)                                      AS goals_for,
       SUM(FTAG)                                      AS goals_against
FROM matches
WHERE HomeTeam = 'Liverpool'
GROUP BY Season
ORDER BY Season;

-- Q3. Highest-scoring months (average goals per match, min. 20 matches)
SELECT strftime('%Y-%m', Date) AS month,
       COUNT(*)                AS matches,
       SUM(TotalGoals)         AS total_goals,
       ROUND(AVG(TotalGoals), 2) AS goals_per_match
FROM matches
GROUP BY month
HAVING matches >= 20
ORDER BY goals_per_match DESC
LIMIT 5;

-- Q4. Home advantage by season (share of matches won by home vs away team)
SELECT Season,
       COUNT(*) AS matches,
       ROUND(100.0 * SUM(CASE WHEN FTR = 'H' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS home_win_pct,
       ROUND(100.0 * SUM(CASE WHEN FTR = 'D' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS draw_pct,
       ROUND(100.0 * SUM(CASE WHEN FTR = 'A' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS away_win_pct
FROM matches
GROUP BY Season
ORDER BY Season;

-- Q5. Teams with the most clean sheets across both seasons combined
SELECT team, COUNT(*) AS clean_sheets
FROM (
    SELECT HomeTeam AS team FROM matches WHERE FTAG = 0
    UNION ALL
    SELECT AwayTeam AS team FROM matches WHERE FTHG = 0
)
GROUP BY team
ORDER BY clean_sheets DESC
LIMIT 5;
