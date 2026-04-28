"""
main.py — Interactive CLI for the League of Legends Stats Database.
Run `python seed.py` first to populate the database.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "loldb.sqlite"

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GOLD   = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
DIM    = "\033[2m"


def connect():
    if not DB_PATH.exists():
        print(f"{RED}Database not found. Run `python seed.py` first.{RESET}")
        exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def banner():
    print(f"""
{GOLD}{BOLD}╔══════════════════════════════════════════╗
║    League of Legends Stats Database     ║
║              loldb v1.0                 ║
╚══════════════════════════════════════════╝{RESET}
""")


def print_table(rows, headers):
    """Pretty-print a list of rows with column headers."""
    if not rows:
        print(f"  {DIM}No results found.{RESET}\n")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val) if val is not None else "—"))

    divider = "  +" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_row = "  |" + "|".join(f" {h:<{w}} " for h, w in zip(headers, col_widths)) + "|"

    print(f"\n{CYAN}{divider}")
    print(header_row)
    print(divider + RESET)
    for row in rows:
        values = [str(v) if v is not None else "—" for v in row]
        print("  |" + "|".join(f" {v:<{w}} " for v, w in zip(values, col_widths)) + "|")
    print(f"{CYAN}{divider}{RESET}")
    print(f"  {DIM}{len(rows)} row(s){RESET}\n")


# ── QUERIES ──────────────────────────────────────────────────────

def top_champions_by_winrate(conn):
    """Top 10 champions by win rate in ranked (min 5 games)."""
    rows = conn.execute("""
        SELECT
            c.name                                              AS Champion,
            c.primary_role                                      AS Role,
            COUNT(*)                                            AS Games,
            SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END) AS Wins,
            ROUND(
                100.0 * SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
                / COUNT(*), 2
            )                                                   AS "Win Rate %"
        FROM match_participants mp
        JOIN champions  c ON mp.champion_id = c.id
        JOIN matches    m ON mp.match_id    = m.id
        WHERE m.game_mode = 'Ranked'
        GROUP BY c.id
        HAVING Games >= 5
        ORDER BY "Win Rate %" DESC
        LIMIT 10
    """).fetchall()
    print_table(rows, ["Champion","Role","Games","Wins","Win Rate %"])


def player_leaderboard(conn):
    """Player leaderboard ranked by LP using window function."""
    rows = conn.execute("""
        SELECT
            RANK() OVER (ORDER BY lp DESC)          AS Rank,
            summoner_name                           AS "Summoner Name",
            region                                  AS Region,
            rank_tier || ' ' || COALESCE(rank_division,'') AS Tier,
            lp                                      AS LP,
            wins                                    AS Wins,
            losses                                  AS Losses,
            ROUND(100.0 * wins / NULLIF(wins+losses,0),1) AS "WR %"
        FROM players
        ORDER BY lp DESC
        LIMIT 20
    """).fetchall()
    print_table(rows, ["Rank","Summoner Name","Region","Tier","LP","Wins","Losses","WR %"])


def best_kda_players(conn):
    """Players with the best overall KDA ratio in ranked."""
    rows = conn.execute("""
        SELECT
            p.summoner_name                         AS "Summoner Name",
            p.rank_tier                             AS Tier,
            COUNT(DISTINCT mp.match_id)             AS Games,
            SUM(mp.kills)                           AS Kills,
            SUM(mp.deaths)                          AS Deaths,
            SUM(mp.assists)                         AS Assists,
            ROUND(
                CAST(SUM(mp.kills)+SUM(mp.assists) AS REAL)
                / NULLIF(SUM(mp.deaths),0), 2
            )                                       AS KDA
        FROM match_participants mp
        JOIN players p ON mp.player_id  = p.id
        JOIN matches m ON mp.match_id   = m.id
        WHERE m.game_mode = 'Ranked'
        GROUP BY p.id
        HAVING Games >= 3
        ORDER BY KDA DESC
        LIMIT 15
    """).fetchall()
    print_table(rows, ["Summoner Name","Tier","Games","Kills","Deaths","Assists","KDA"])


def champion_performance_by_patch(conn):
    """Win rate per champion per patch using a CTE + LAG window function."""
    rows = conn.execute("""
        WITH patch_perf AS (
            SELECT
                c.name                              AS champion,
                m.patch,
                COUNT(*)                            AS games,
                SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END) AS wins,
                ROUND(
                    100.0 * SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
                    / COUNT(*), 1
                )                                   AS win_rate
            FROM match_participants mp
            JOIN champions c ON mp.champion_id = c.id
            JOIN matches   m ON mp.match_id    = m.id
            WHERE m.game_mode = 'Ranked'
            GROUP BY c.id, m.patch
        )
        SELECT
            champion                                AS Champion,
            patch                                   AS Patch,
            games                                   AS Games,
            win_rate                                AS "WR %",
            ROUND(
                win_rate - LAG(win_rate)
                    OVER (PARTITION BY champion ORDER BY patch), 1
            )                                       AS "Change"
        FROM patch_perf
        ORDER BY champion, patch
        LIMIT 50
    """).fetchall()
    print_table(rows, ["Champion","Patch","Games","WR %","Change"])


def most_popular_items(conn):
    """Most built items across all matches."""
    rows = conn.execute("""
        WITH all_items AS (
            SELECT item1_id AS iid FROM match_participants WHERE item1_id IS NOT NULL UNION ALL
            SELECT item2_id FROM match_participants WHERE item2_id IS NOT NULL UNION ALL
            SELECT item3_id FROM match_participants WHERE item3_id IS NOT NULL UNION ALL
            SELECT item4_id FROM match_participants WHERE item4_id IS NOT NULL UNION ALL
            SELECT item5_id FROM match_participants WHERE item5_id IS NOT NULL UNION ALL
            SELECT item6_id FROM match_participants WHERE item6_id IS NOT NULL
        )
        SELECT
            i.name                          AS Item,
            i.category                      AS Category,
            i.cost                          AS Cost,
            COUNT(*)                        AS "Times Built",
            RANK() OVER (ORDER BY COUNT(*) DESC) AS Rank
        FROM all_items ai
        JOIN items i ON i.id = ai.iid
        GROUP BY i.id
        ORDER BY "Times Built" DESC
        LIMIT 15
    """).fetchall()
    print_table(rows, ["Item","Category","Cost","Times Built","Rank"])


def avg_stats_by_position(conn):
    """Average KDA, CS, damage, gold per position in ranked games."""
    rows = conn.execute("""
        SELECT
            mp.position                         AS Position,
            ROUND(AVG(mp.kills),2)              AS "Avg Kills",
            ROUND(AVG(mp.deaths),2)             AS "Avg Deaths",
            ROUND(AVG(mp.assists),2)            AS "Avg Assists",
            ROUND(AVG(mp.cs),1)                 AS "Avg CS",
            ROUND(AVG(mp.damage_dealt))         AS "Avg Damage",
            ROUND(AVG(mp.gold_earned))          AS "Avg Gold",
            ROUND(AVG(mp.vision_score),1)       AS "Avg Vision",
            COUNT(*)                            AS Samples
        FROM match_participants mp
        JOIN matches m ON mp.match_id = m.id
        WHERE m.game_mode = 'Ranked'
        GROUP BY mp.position
        ORDER BY "Avg Damage" DESC
    """).fetchall()
    print_table(rows, ["Position","Avg Kills","Avg Deaths","Avg Assists","Avg CS","Avg Damage","Avg Gold","Avg Vision","Samples"])


def champion_synergy(conn):
    """Champion pairs with the highest win rate when on the same team."""
    rows = conn.execute("""
        SELECT
            c1.name                             AS "Champion 1",
            c2.name                             AS "Champion 2",
            COUNT(*)                            AS "Games Together",
            SUM(CASE WHEN mp1.team = m.winning_team THEN 1 ELSE 0 END) AS Wins,
            ROUND(
                100.0 * SUM(CASE WHEN mp1.team = m.winning_team THEN 1 ELSE 0 END)
                / COUNT(*), 1
            )                                   AS "Win Rate %"
        FROM match_participants mp1
        JOIN match_participants mp2
            ON  mp1.match_id = mp2.match_id
            AND mp1.team     = mp2.team
            AND mp1.id       < mp2.id
        JOIN champions c1 ON mp1.champion_id = c1.id
        JOIN champions c2 ON mp2.champion_id = c2.id
        JOIN matches   m  ON mp1.match_id    = m.id
        WHERE m.game_mode = 'Ranked'
        GROUP BY c1.id, c2.id
        HAVING "Games Together" >= 2
        ORDER BY "Win Rate %" DESC
        LIMIT 15
    """).fetchall()
    print_table(rows, ["Champion 1","Champion 2","Games Together","Wins","Win Rate %"])


def player_match_history(conn):
    """Show full match history for a specific player."""
    name = input(f"  {CYAN}Enter summoner name: {RESET}").strip()
    rows = conn.execute("""
        SELECT
            m.game_id                               AS "Game ID",
            m.patch                                 AS Patch,
            m.game_mode                             AS Mode,
            ROUND(m.duration_secs/60.0,1)           AS "Mins",
            c.name                                  AS Champion,
            mp.position                             AS Position,
            mp.kills || '/' || mp.deaths || '/' || mp.assists AS KDA,
            mp.cs                                   AS CS,
            mp.damage_dealt                         AS Damage,
            CASE WHEN mp.team = m.winning_team THEN 'WIN' ELSE 'LOSS' END AS Result
        FROM match_participants mp
        JOIN matches   m ON mp.match_id    = m.id
        JOIN champions c ON mp.champion_id = c.id
        JOIN players   p ON mp.player_id   = p.id
        WHERE p.summoner_name = ?
        ORDER BY m.played_at DESC
    """, (name,)).fetchall()
    if not rows:
        print(f"  {RED}No data found for '{name}'. Try: CarryGod9{RESET}\n")
    else:
        print_table(rows, ["Game ID","Patch","Mode","Mins","Champion","Position","KDA","CS","Damage","Result"])


def stomp_detection(conn):
    """Find matches where the winning team dominated by damage dealt."""
    rows = conn.execute("""
        WITH team_dmg AS (
            SELECT match_id, team, SUM(damage_dealt) AS total_damage
            FROM match_participants
            GROUP BY match_id, team
        )
        SELECT
            m.game_id                               AS "Game ID",
            m.patch                                 AS Patch,
            ROUND(m.duration_secs/60.0,1)           AS "Mins",
            CASE m.winning_team WHEN 1 THEN 'Blue' ELSE 'Red' END AS Winner,
            td1.total_damage                        AS "Blue Damage",
            td2.total_damage                        AS "Red Damage",
            ABS(td1.total_damage - td2.total_damage) AS "Gap"
        FROM matches m
        JOIN team_dmg td1 ON td1.match_id = m.id AND td1.team = 1
        JOIN team_dmg td2 ON td2.match_id = m.id AND td2.team = 2
        ORDER BY "Gap" DESC
        LIMIT 10
    """).fetchall()
    print_table(rows, ["Game ID","Patch","Mins","Winner","Blue Damage","Red Damage","Gap"])


def database_summary(conn):
    """Show a quick summary of what's in the database."""
    counts = {
        "Champions":        conn.execute("SELECT COUNT(*) FROM champions").fetchone()[0],
        "Items":            conn.execute("SELECT COUNT(*) FROM items").fetchone()[0],
        "Players":          conn.execute("SELECT COUNT(*) FROM players").fetchone()[0],
        "Matches":          conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0],
        "Participant rows": conn.execute("SELECT COUNT(*) FROM match_participants").fetchone()[0],
    }
    print()
    for label, count in counts.items():
        print(f"  {CYAN}{label:<20}{RESET} {GOLD}{BOLD}{count}{RESET}")
    print()


# ── MENU ─────────────────────────────────────────────────────────

MENU = [
    ("Top Champions by Win Rate",        top_champions_by_winrate),
    ("Player Leaderboard (LP Ranked)",   player_leaderboard),
    ("Best KDA Players",                 best_kda_players),
    ("Champion Performance by Patch",    champion_performance_by_patch),
    ("Most Popular Items",               most_popular_items),
    ("Average Stats by Position",        avg_stats_by_position),
    ("Champion Synergy Pairs",           champion_synergy),
    ("Player Match History",             player_match_history),
    ("Stomp Detection (Biggest Gaps)",   stomp_detection),
    ("Database Summary",                 database_summary),
]


def show_menu():
    print(f"{CYAN}{BOLD}  Select a query:{RESET}")
    for i, (label, _) in enumerate(MENU, 1):
        print(f"  {GOLD}{i:>2}.{RESET} {label}")
    print(f"  {DIM} 0.  Exit{RESET}")
    print()


def main():
    banner()
    conn = connect()

    while True:
        show_menu()
        choice = input(f"  {CYAN}> {RESET}").strip()

        if choice == "0":
            print(f"\n{GOLD}GG WP. See you on the Rift. 🎮{RESET}\n")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU):
                label, fn = MENU[idx]
                print(f"\n{BOLD}{CYAN}── {label} ──{RESET}")
                fn(conn)
            else:
                print(f"  {RED}Invalid option.{RESET}\n")
        except ValueError:
            print(f"  {RED}Please enter a number.{RESET}\n")

    conn.close()


if __name__ == "__main__":
    main()
