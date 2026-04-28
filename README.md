# loldb — League of Legends Stats Database

A relational database project built around League of Legends match data. Designed to show real-world SQL skills: complex multi-table JOINs, window functions, CTEs, subqueries, and aggregations — all on a dataset that actually makes sense.

Built with **SQLite** and a **Python CLI** on top. No ORM — raw SQL throughout so every query is readable and intentional.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat&logo=sqlite&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-Raw%20Queries-orange?style=flat)

---

## What It Does

- Stores champions, players, matches, match participants, and items across a normalized relational schema
- Seeds realistic demo data (100 matches, 30 players, 20 champions, 19 items)
- Runs 10 analytical queries from an interactive CLI menu
- Includes a `sql/` folder with standalone `.sql` files — readable as plain SQL without running anything

---

## Project Structure

```
loldb/
├── main.py                    # Interactive CLI — run queries from a menu
├── seed.py                    # Seeds the database with demo data
├── requirements.txt           # No pip install needed (stdlib only)
├── .gitignore
├── sql/
│   ├── schema.sql             # All CREATE TABLE definitions + indexes
│   └── queries/
│       └── showcase.sql       # 10 standalone analytical SQL queries
└── README.md
```

---

## Getting Started

### Requirements

- Python 3.8 or later (no third-party packages needed)

### Run It

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/loldb.git
cd loldb

# 2. Seed the database (run once)
python seed.py

# 3. Start the interactive CLI
python main.py
```

---

## CLI Menu

```
  Select a query:
   1.  Top Champions by Win Rate
   2.  Player Leaderboard (LP Ranked)
   3.  Best KDA Players
   4.  Champion Performance by Patch
   5.  Most Popular Items
   6.  Average Stats by Position
   7.  Champion Synergy Pairs
   8.  Player Match History
   9.  Stomp Detection (Biggest Gaps)
  10.  Database Summary
   0.  Exit
```

---

## Database Schema

### Tables

| Table | Description |
|-------|-------------|
| `champions` | All champions with role, class, win/pick/ban rates |
| `items` | Items with cost, category, and stat bonuses |
| `players` | Summoner accounts with rank, LP, wins, losses |
| `matches` | Individual games with patch, mode, duration, winner |
| `match_participants` | One row per player per game — KDA, CS, damage, items |
| `champion_patch_stats` | Aggregated champion performance per patch |

### Relationships

```
players ──< match_participants >── matches
champions ─< match_participants
items ──────< match_participants (item1–6)
champions ──< champion_patch_stats
```

---

## SQL Features Showcased

| Concept | Where Used |
|---------|-----------|
| Multi-table `JOIN` | Every query — participants + matches + champions + players |
| `GROUP BY` + `HAVING` | Win rate queries (filter by minimum games played) |
| `CASE WHEN` | Calculating wins from team number vs winning_team |
| `NULLIF` | Safe division — avoiding divide-by-zero in KDA / win rate |
| `COALESCE` | Handling NULL rank divisions for Master+ players |
| `WITH` (CTE) | Patch performance trends, stomp detection, item counts |
| `RANK() OVER` | Player leaderboard, item popularity ranking |
| `LAG() OVER (PARTITION BY ... ORDER BY ...)` | Win rate change between patches per champion |
| Self-join | Champion synergy — pairing teammates within the same match |
| `UNION ALL` | Flattening item slots (item1–6) into a single column |
| `CREATE INDEX` | Indexes on foreign keys and common filter columns |
| `CHECK` constraints | Enforcing valid enums (rank tier, game mode, position) |
| `ON DELETE CASCADE` | Deleting a match removes all its participant rows |
| `UNIQUE` constraints | Preventing duplicate participants per match |

---

## Example Query — Champion Synergy (Self-Join)

```sql
SELECT
    c1.name                                     AS "Champion 1",
    c2.name                                     AS "Champion 2",
    COUNT(*)                                    AS "Games Together",
    ROUND(
        100.0 * SUM(CASE WHEN mp1.team = m.winning_team THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                                           AS "Win Rate %"
FROM match_participants mp1
JOIN match_participants mp2
    ON  mp1.match_id = mp2.match_id
    AND mp1.team     = mp2.team
    AND mp1.id       < mp2.id        -- avoid duplicate pairs
JOIN champions c1 ON mp1.champion_id = c1.id
JOIN champions c2 ON mp2.champion_id = c2.id
JOIN matches   m  ON mp1.match_id    = m.id
WHERE m.game_mode = 'Ranked'
GROUP BY c1.id, c2.id
HAVING "Games Together" >= 2
ORDER BY "Win Rate %" DESC;
```

---

## Example Query — Patch Win Rate Trend (CTE + Window Function)

```sql
WITH patch_perf AS (
    SELECT
        c.name  AS champion,
        m.patch,
        COUNT(*) AS games,
        ROUND(
            100.0 * SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )       AS win_rate
    FROM match_participants mp
    JOIN champions c ON mp.champion_id = c.id
    JOIN matches   m ON mp.match_id    = m.id
    GROUP BY c.id, m.patch
)
SELECT
    champion,
    patch,
    win_rate,
    win_rate - LAG(win_rate) OVER (PARTITION BY champion ORDER BY patch) AS change
FROM patch_perf
ORDER BY champion, patch;
```

---

## Built With

| Technology | Role |
|---|---|
| Python 3.8+ | CLI, seeding, query runner |
| SQLite 3 | Embedded relational database |
| `sqlite3` (stdlib) | Database connection — raw SQL, no ORM |
| `pathlib` (stdlib) | Cross-platform file paths |

---

## What I Learned

- Designing a normalized relational schema from scratch with proper foreign keys, constraints, and indexes
- Writing complex analytical SQL — window functions, CTEs, self-joins, and aggregate filtering with HAVING
- Using `RANK()` and `LAG()` window functions for leaderboards and trend analysis
- Handling NULL safely in division using `NULLIF` to avoid runtime errors
- Seeding a realistic dataset programmatically to make queries meaningful
- Separating schema, seed data, and application logic into distinct, readable files
- Building a menu-driven Python CLI that runs raw SQL and formats results without any framework
