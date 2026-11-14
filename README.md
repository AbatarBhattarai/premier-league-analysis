# Premier League Data Analysis

**By Abatar Bhattarai**

I analysed two full Premier League seasons — 2023/24 and 2024/25 — to look
at scoring trends, home advantage, the best attacks and defences, and (as a
Liverpool fan) how Liverpool went from third place to champions.

## Data source

Match results downloaded from [football-data.co.uk](https://www.football-data.co.uk),
which publishes free CSV files of match data for research use:

- `data/E0_2023-24.csv` — 2023/24 season (380 matches)
- `data/E0_2024-25.csv` — 2024/25 season (380 matches)

Credit to football-data.co.uk for making this data available. I only use
the result columns (date, teams, goals, result) and ignore the betting
odds columns in the files.

## Tools

- **Python (pandas)** — cleaning, combining the seasons, all calculations
- **SQL (SQLite)** — the same questions answered with queries against a
  database built from the cleaned data
- **matplotlib** — charts

## Files

| File | What it is |
| --- | --- |
| `analysis.py` | Loads and cleans both seasons, computes every result, saves the outputs and builds the charts |
| `queries.sql` | 5 SQL questions: top attacks, Liverpool's home record, highest-scoring months, home advantage by season, most clean sheets |
| `data/matches_combined.csv` | Cleaned combined dataset (760 matches) |
| `team_season_table.csv` | Full per-team table for each season (position, W/D/L, goals, points, clean sheets) |
| `premier_league.db` | SQLite database created by `analysis.py` (tables: `matches`, `team_season`) |
| `charts/` | Monthly goals trend, goals per season, top attacks vs defences, Liverpool results breakdown |
| `insights.md` | The findings written up in plain language |

## How to run

```bash
python analysis.py          # prints all results, rebuilds data + charts
sqlite3 premier_league.db < queries.sql
```

## Headline findings

- **760 matches, 2,361 goals, 3.11 goals per match** across the two seasons.
- Scoring fell in 2024/25: **3.28 goals per match in 2023/24 down to 2.93**
  in 2024/25, driven by home teams scoring less.
- **Home advantage shrank**: home wins dropped from 46.1% (2023/24) to
  40.8% (2024/25), while away wins and draws both rose.
- **Best attacks:** Man City scored 96 in 2023/24; Liverpool scored 86 in
  2024/25 and the most across both seasons combined (172).
- **Best defence both seasons: Arsenal** (29 goals conceded in 2023/24,
  34 in 2024/25), and the most clean sheets overall (31).
- **Liverpool:** 3rd with 82 points in 2023/24, **champions with 84 points
  in 2024/25** — with identical goals for (86) and against (41) in both
  seasons. They lost just one home game each season, and their clean
  sheets jumped from 10 to a league-best 14 in the title season.
- The highest-scoring month in the dataset was **February 2024: 3.76
  goals per match**.

Full write-up in `insights.md`.
