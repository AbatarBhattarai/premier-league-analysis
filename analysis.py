"""
Premier League Analysis - 2023/24 and 2024/25 seasons
Data source: football-data.co.uk (E0.csv files)

What this script does:
  1. Loads and cleans both season files, combines them into one dataset
  2. Computes result rates, goals, team attack/defence tables, and a
     Liverpool section
  3. Saves a cleaned combined CSV and loads it into SQLite
  4. Builds the charts used in the README and insights

Run: python analysis.py
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).parent
DATA = BASE / "data"
CHARTS = BASE / "charts"
CHARTS.mkdir(exist_ok=True)

SEASON_FILES = {
    "2023/24": DATA / "E0_2023-24.csv",
    "2024/25": DATA / "E0_2024-25.csv",
}

KEEP = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]


def load_seasons() -> pd.DataFrame:
    frames = []
    for season, path in SEASON_FILES.items():
        df = pd.read_csv(path, usecols=lambda c: c in KEEP)
        df["Season"] = season
        frames.append(df)
    matches = pd.concat(frames, ignore_index=True)

    # Clean: parse dates, force goal columns numeric, drop incomplete rows
    matches["Date"] = pd.to_datetime(matches["Date"], dayfirst=True)
    matches["FTHG"] = pd.to_numeric(matches["FTHG"], errors="coerce")
    matches["FTAG"] = pd.to_numeric(matches["FTAG"], errors="coerce")
    before = len(matches)
    matches = matches.dropna(subset=["FTHG", "FTAG", "FTR"]).copy()
    matches["FTHG"] = matches["FTHG"].astype(int)
    matches["FTAG"] = matches["FTAG"].astype(int)
    matches["TotalGoals"] = matches["FTHG"] + matches["FTAG"]
    matches["Month"] = matches["Date"].dt.to_period("M").dt.to_timestamp()
    print(f"Loaded {before} rows, kept {len(matches)} clean matches "
          f"({before - len(matches)} dropped)")
    return matches


def result_rates(matches: pd.DataFrame) -> None:
    print("\n=== RESULT RATES BY SEASON ===")
    for season, g in matches.groupby("Season"):
        n = len(g)
        home = (g["FTR"] == "H").mean() * 100
        draw = (g["FTR"] == "D").mean() * 100
        away = (g["FTR"] == "A").mean() * 100
        print(f"{season}: {n} matches | home wins {home:.1f}% | "
              f"draws {draw:.1f}% | away wins {away:.1f}%")
    n = len(matches)
    print(f"COMBINED: {n} matches | home wins "
          f"{(matches['FTR'] == 'H').mean() * 100:.1f}% | draws "
          f"{(matches['FTR'] == 'D').mean() * 100:.1f}% | away wins "
          f"{(matches['FTR'] == 'A').mean() * 100:.1f}%")


def goals_per_match(matches: pd.DataFrame) -> None:
    print("\n=== GOALS PER MATCH ===")
    for season, g in matches.groupby("Season"):
        print(f"{season}: {g['TotalGoals'].sum()} total goals, "
              f"{g['TotalGoals'].mean():.2f} per match "
              f"(home {g['FTHG'].mean():.2f}, away {g['FTAG'].mean():.2f})")
    print(f"COMBINED: {matches['TotalGoals'].sum()} total goals, "
          f"{matches['TotalGoals'].mean():.2f} per match")


def team_table(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per team per season: played, W/D/L, GF, GA, points."""
    rows = []
    for season, g in matches.groupby("Season"):
        for team in sorted(set(g["HomeTeam"]) | set(g["AwayTeam"])):
            home = g[g["HomeTeam"] == team]
            away = g[g["AwayTeam"] == team]
            gf = home["FTHG"].sum() + away["FTAG"].sum()
            ga = home["FTAG"].sum() + away["FTHG"].sum()
            wins = (home["FTR"] == "H").sum() + (away["FTR"] == "A").sum()
            draws = ((home["FTR"] == "D").sum()
                     + (away["FTR"] == "D").sum())
            losses = len(home) + len(away) - wins - draws
            rows.append({
                "Season": season, "Team": team,
                "Played": len(home) + len(away),
                "Won": int(wins), "Drawn": int(draws),
                "Lost": int(losses),
                "GF": int(gf), "GA": int(ga), "GD": int(gf - ga),
                "Points": int(wins * 3 + draws),
                "CleanSheets": int((home["FTAG"] == 0).sum()
                                   + (away["FTHG"] == 0).sum()),
            })
    table = pd.DataFrame(rows).sort_values(
        ["Season", "Points", "GD", "GF"], ascending=[True, False, False, False])
    table["Position"] = table.groupby("Season").cumcount() + 1
    return table


def print_team_tables(table: pd.DataFrame) -> None:
    print("\n=== BEST ATTACKS (goals scored, per season) ===")
    for season, g in table.groupby("Season"):
        top = g.nlargest(5, "GF")
        print(f"{season}: " + ", ".join(
            f"{r.Team} {r.GF}" for r in top.itertuples()))
    print("\n=== BEST DEFENCES (fewest goals conceded, per season) ===")
    for season, g in table.groupby("Season"):
        top = g.nsmallest(5, "GA")
        print(f"{season}: " + ", ".join(
            f"{r.Team} {r.GA}" for r in top.itertuples()))
    print("\n=== MOST CLEAN SHEETS (per season) ===")
    for season, g in table.groupby("Season"):
        top = g.nlargest(3, "CleanSheets")
        print(f"{season}: " + ", ".join(
            f"{r.Team} {r.CleanSheets}" for r in top.itertuples()))
    print("\n=== CHAMPIONS / TOP 3 (per season) ===")
    for season, g in table.groupby("Season"):
        top = g.nsmallest(3, "Position")
        print(f"{season}: " + ", ".join(
            f"{r.Position}. {r.Team} ({r.Points} pts)"
            for r in top.itertuples()))


def liverpool_section(matches: pd.DataFrame, table: pd.DataFrame) -> None:
    print("\n=== LIVERPOOL ===")
    liv_t = table[table["Team"] == "Liverpool"]
    for r in liv_t.itertuples():
        print(f"{r.Season}: finished {r.Position} with {r.Points} points | "
              f"W{r.Won} D{r.Drawn} L{r.Lost} | GF {r.GF}, GA {r.GA} "
              f"(GD {r.GD:+d}) | clean sheets {r.CleanSheets}")
    liv = matches[(matches["HomeTeam"] == "Liverpool")
                  | (matches["AwayTeam"] == "Liverpool")]
    for season, g in liv.groupby("Season"):
        home = g[g["HomeTeam"] == "Liverpool"]
        away = g[g["AwayTeam"] == "Liverpool"]
        hw = (home["FTR"] == "H").sum(); hd = (home["FTR"] == "D").sum()
        hl = (home["FTR"] == "A").sum()
        aw = (away["FTR"] == "A").sum(); ad = (away["FTR"] == "D").sum()
        al = (away["FTR"] == "H").sum()
        print(f"{season} home: W{hw} D{hd} L{hl} "
              f"(GF {home['FTHG'].sum()}, GA {home['FTAG'].sum()}) | "
              f"away: W{aw} D{ad} L{al} "
              f"(GF {away['FTAG'].sum()}, GA {away['FTHG'].sum()})")
    big = liv[(liv["FTHG"] + liv["FTAG"]) >= 5].sort_values("Date")
    print(f"Liverpool matches with 5+ total goals: {len(big)} of {len(liv)}")


def monthly_goals(matches: pd.DataFrame) -> pd.DataFrame:
    m = (matches.groupby("Month")["TotalGoals"]
         .agg(["sum", "count", "mean"]).reset_index())
    print("\n=== HIGHEST-SCORING MONTHS (avg goals per match) ===")
    top = m.nlargest(5, "mean")
    for r in top.itertuples():
        print(f"{r.Month:%Y-%m}: {r.mean:.2f} per match "
              f"({int(r.sum)} goals in {int(r.count)} matches)")
    return m


def save_outputs(matches: pd.DataFrame, table: pd.DataFrame) -> None:
    out = matches[["Season", "Date", "HomeTeam", "AwayTeam",
                   "FTHG", "FTAG", "FTR", "TotalGoals"]].copy()
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA / "matches_combined.csv", index=False)
    table.to_csv(BASE / "team_season_table.csv", index=False)

    db_path = BASE / "premier_league.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    out.to_sql("matches", con, index=False)
    table.to_sql("team_season", con, index=False)
    con.close()
    print(f"\nSaved data/matches_combined.csv ({len(out)} rows), "
          f"team_season_table.csv, and premier_league.db "
          f"(tables: matches, team_season)")


def make_charts(matches: pd.DataFrame, table: pd.DataFrame,
                monthly: pd.DataFrame) -> None:
    # 1. Monthly goals trend (avg goals per match, both seasons combined)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly["Month"], monthly["mean"], marker="o", color="#1f77b4")
    ax.set_title("Average goals per match by month (2023/24 + 2024/25)")
    ax.set_ylabel("Goals per match")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS / "monthly_goals.png", dpi=120)
    plt.close(fig)

    # 2. Goals per season
    g = matches.groupby("Season")["TotalGoals"].mean()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(g.index, g.values, color=["#7f7f7f", "#c8102e"])
    for i, v in enumerate(g.values):
        ax.text(i, v + 0.03, f"{v:.2f}", ha="center")
    ax.set_title("Average goals per match by season")
    ax.set_ylabel("Goals per match")
    ax.set_ylim(0, max(g.values) * 1.2)
    fig.tight_layout()
    fig.savefig(CHARTS / "goals_per_season.png", dpi=120)
    plt.close(fig)

    # 3. Top attacks vs their defences (both seasons combined)
    comb = (table.groupby("Team")[["GF", "GA"]].sum()
            .nlargest(8, "GF").sort_values("GF"))
    fig, ax = plt.subplots(figsize=(9, 5))
    y = range(len(comb))
    ax.barh([i + 0.2 for i in y], comb["GF"], height=0.4,
            label="Goals scored", color="#2ca02c")
    ax.barh([i - 0.2 for i in y], comb["GA"], height=0.4,
            label="Goals conceded", color="#d62728")
    ax.set_yticks(list(y))
    ax.set_yticklabels(comb.index)
    ax.set_title("Top 8 attacks, 2023/24 + 2024/25 combined - "
                 "goals scored vs conceded")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "top_attacks_vs_defences.png", dpi=120)
    plt.close(fig)

    # 4. Liverpool results breakdown (home vs away, both seasons combined)
    liv = matches[(matches["HomeTeam"] == "Liverpool")
                  | (matches["AwayTeam"] == "Liverpool")]
    home = liv[liv["HomeTeam"] == "Liverpool"]
    away = liv[liv["AwayTeam"] == "Liverpool"]
    data = {
        "Home": [(home["FTR"] == "H").sum(), (home["FTR"] == "D").sum(),
                 (home["FTR"] == "A").sum()],
        "Away": [(away["FTR"] == "A").sum(), (away["FTR"] == "D").sum(),
                 (away["FTR"] == "H").sum()],
    }
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = ["Won", "Drawn", "Lost"]
    colors = ["#2ca02c", "#ffbf00", "#d62728"]
    for i, venue in enumerate(["Home", "Away"]):
        left = 0
        for j, lab in enumerate(labels):
            ax.barh(venue, data[venue][j], left=left, color=colors[j],
                    label=lab if i == 0 else "")
            ax.text(left + data[venue][j] / 2, i, str(data[venue][j]),
                    ha="center", va="center", color="white",
                    fontweight="bold")
            left += data[venue][j]
    ax.set_title("Liverpool results, 2023/24 + 2024/25 (76 matches)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(CHARTS / "liverpool_results.png", dpi=120)
    plt.close(fig)
    print(f"Charts saved to {CHARTS}")


def main() -> None:
    matches = load_seasons()
    result_rates(matches)
    goals_per_match(matches)
    table = team_table(matches)
    print_team_tables(table)
    liverpool_section(matches, table)
    monthly = monthly_goals(matches)
    save_outputs(matches, table)
    make_charts(matches, table, monthly)


if __name__ == "__main__":
    main()
