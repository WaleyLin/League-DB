"""
seed.py — Populates the database with realistic League of Legends demo data.
Run this once before using main.py.
"""

import sqlite3
import random
from pathlib import Path

DB_PATH     = Path(__file__).parent / "loldb.sqlite"
SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def run_schema(conn):
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    print("  ✓ Schema applied")


# ── SEED DATA ────────────────────────────────────────────────────

CHAMPIONS = [
    ("Jinx",      "The Loose Cannon",    "Marksman", "Bot",     2013),
    ("Yasuo",     "The Unforgiven",       "Fighter",  "Mid",     2013),
    ("Thresh",    "The Chain Warden",     "Support",  "Support", 2013),
    ("Lee Sin",   "The Blind Monk",       "Fighter",  "Jungle",  2012),
    ("Ahri",      "The Nine-Tailed Fox",  "Mage",     "Mid",     2011),
    ("Darius",    "The Hand of Noxus",    "Fighter",  "Top",     2012),
    ("Ezreal",    "The Prodigal Explorer","Marksman", "Bot",     2010),
    ("Lulu",      "The Fae Sorceress",    "Support",  "Support", 2012),
    ("Zed",       "The Master of Shadows","Assassin", "Mid",     2012),
    ("Vi",        "The Piltover Enforcer","Fighter",  "Jungle",  2012),
    ("Caitlyn",   "The Sheriff of Piltover","Marksman","Bot",    2011),
    ("Nautilus",  "The Titan of the Depths","Tank",   "Support", 2012),
    ("Lux",       "The Lady of Luminosity","Mage",    "Support", 2010),
    ("Garen",     "The Might of Demacia", "Fighter",  "Top",     2010),
    ("Akali",     "The Rogue Assassin",   "Assassin", "Mid",     2010),
    ("Jhin",      "The Virtuoso",         "Marksman", "Bot",     2016),
    ("Hecarim",   "The Shadow of War",    "Fighter",  "Jungle",  2012),
    ("Orianna",   "The Lady of Clockwork","Mage",     "Mid",     2012),
    ("Malphite",  "Shard of the Monolith","Tank",     "Top",     2009),
    ("Blitzcrank","The Great Steam Golem","Tank",     "Support", 2009),
]

ITEMS = [
    # Mythics
    ("Trinity Force",       3333, "Mythic",    30, 0,  200, 0,  0,  0.0, 0),
    ("Luden's Tempest",     3200, "Mythic",    0,  100,0,  0,  0,  0.0, 0),
    ("Kraken Slayer",       3400, "Mythic",    65, 0,  0,  0,  0,  25.0,0),
    ("Sunfire Aegis",       3200, "Mythic",    0,  0,  450,50, 0,  0.0, 0),
    ("Galeforce",           3400, "Mythic",    55, 0,  0,  0,  0,  0.0, 20),
    ("Liandry's Anguish",   3000, "Mythic",    0,  90, 300,0,  0,  0.0, 0),
    # Legendaries
    ("Rabadon's Deathcap",  3800, "Legendary", 0,  120,0,  0,  0,  0.0, 0),
    ("Infinity Edge",       3400, "Legendary", 70, 0,  0,  0,  0,  0.0, 20),
    ("Frozen Heart",        2500, "Legendary", 0,  0,  0,  80, 0,  0.0, 0),
    ("Warmog's Armor",      3100, "Legendary", 0,  0,  800,0,  0,  0.0, 0),
    ("Shadowflame",         3200, "Legendary", 0,  100,250,0,  0,  0.0, 0),
    ("Zhonya's Hourglass",  2900, "Legendary", 0,  65, 0,  45, 0,  0.0, 0),
    # Epics
    ("Blasting Wand",       850,  "Epic",      0,  40, 0,  0,  0,  0.0, 0),
    ("B.F. Sword",          1300, "Epic",      40, 0,  0,  0,  0,  0.0, 0),
    ("Chain Vest",          800,  "Epic",      0,  0,  0,  40, 0,  0.0, 0),
    # Boots
    ("Sorcerer's Shoes",    1100, "Boots",     0,  18, 0,  0,  0,  0.0, 0),
    ("Berserker's Greaves", 1100, "Boots",     0,  0,  0,  0,  0,  35.0,0),
    ("Plated Steelcaps",    1100, "Boots",     0,  0,  0,  20, 0,  0.0, 0),
    ("Mercury's Treads",    1100, "Boots",     0,  0,  0,  0,  25, 0.0, 0),
]

SUMMONER_NAMES = [
    "CarryGod9","xX_Yasuo_Xx","SupportMain","JungleGap","ADCPro",
    "MidOrFeed","TopFragger","OnetrckPony","Diamond4Life","EloHell",
    "NightCrawler","SilverSurfer","GoldMiner","PlatKing","EmeGod",
    "FlashOrDie","IgniteLife","TeleportBot","SmiteJungle","ExhaustSup",
    "BlueTeamWin","RedSideOP","DragonStealer","BaronCaller","HeraldBoy",
    "VistarBot","CritChanceGo","ArmorPenetrate","MagicPenLord","TrueD4mage",
]

REGIONS       = ["NA","EUW","KR","EUW","NA","EUW"]
RANK_TIERS    = ["Iron","Bronze","Silver","Gold","Platinum","Emerald","Diamond","Master"]
RANK_DIVS     = ["I","II","III","IV"]
PATCHES       = ["14.6","14.7","14.8","14.9","14.10"]
GAME_MODES    = ["Ranked","Ranked","Ranked","Normal","ARAM"]
POSITIONS     = ["Top","Jungle","Mid","Bot","Support"]


def seed_champions(conn):
    rows = []
    for name, title, cls, role, year in CHAMPIONS:
        wr = round(random.uniform(47.0, 54.5), 2)
        pr = round(random.uniform(3.0, 18.0), 2)
        br = round(random.uniform(1.0, 12.0), 2)
        rows.append((name, title, cls, role, year, pr, br, wr))
    conn.executemany(
        "INSERT OR IGNORE INTO champions (name,title,class,primary_role,release_year,pick_rate,ban_rate,win_rate)"
        " VALUES (?,?,?,?,?,?,?,?)",
        rows
    )
    print(f"  ✓ Inserted {len(rows)} champions")


def seed_items(conn):
    conn.executemany(
        "INSERT OR IGNORE INTO items (name,cost,category,stat_ad,stat_ap,stat_hp,stat_armor,stat_mr,stat_as,stat_crit)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        ITEMS
    )
    print(f"  ✓ Inserted {len(ITEMS)} items")


def seed_players(conn):
    rows = []
    for name in SUMMONER_NAMES:
        tier = random.choice(RANK_TIERS)
        div  = None if tier in ("Master","Grandmaster","Challenger") else random.choice(RANK_DIVS)
        lp   = random.randint(0, 99) if div else random.randint(200, 1500)
        w    = random.randint(50, 400)
        l    = random.randint(40, 380)
        rows.append((name, random.choice(REGIONS), tier, div, lp, w, l))
    conn.executemany(
        "INSERT OR IGNORE INTO players (summoner_name,region,rank_tier,rank_division,lp,wins,losses)"
        " VALUES (?,?,?,?,?,?,?)",
        rows
    )
    print(f"  ✓ Inserted {len(rows)} players")


def seed_matches(conn, n=80):
    """Generate n matches, each with 10 participants."""
    cur         = conn.cursor()
    champ_ids   = [r[0] for r in cur.execute("SELECT id FROM champions").fetchall()]
    player_ids  = [r[0] for r in cur.execute("SELECT id FROM players").fetchall()]
    item_ids    = [r[0] for r in cur.execute("SELECT id FROM items").fetchall()]

    matches_inserted = 0
    participants_inserted = 0

    for i in range(n):
        patch       = random.choice(PATCHES)
        mode        = random.choice(GAME_MODES)
        duration    = random.randint(18 * 60, 48 * 60)
        winning_team= random.choice([1, 2])
        game_id     = f"NA1_{10000000 + i}"
        played_at   = f"2024-0{random.randint(1,9)}-{random.randint(1,28):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:00"

        cur.execute(
            "INSERT OR IGNORE INTO matches (game_id,patch,game_mode,duration_secs,winning_team,played_at)"
            " VALUES (?,?,?,?,?,?)",
            (game_id, patch, mode, duration, winning_team, played_at)
        )
        match_id = cur.lastrowid
        if not match_id:
            continue
        matches_inserted += 1

        # Pick 10 unique players and 10 unique (per team) champions
        chosen_players = random.sample(player_ids, min(10, len(player_ids)))
        chosen_champs  = random.sample(champ_ids,  min(10, len(champ_ids)))

        for slot, (pid, cid) in enumerate(zip(chosen_players, chosen_champs)):
            team     = 1 if slot < 5 else 2
            position = POSITIONS[slot % 5]
            kills    = random.randint(0, 18)
            deaths   = random.randint(0, 12)
            assists  = random.randint(0, 20)
            cs       = random.randint(80, 340)
            dmg      = random.randint(8000, 65000)
            dmg_taken= random.randint(5000, 45000)
            gold     = random.randint(7000, 21000)
            vision   = random.randint(10, 90)
            p_items  = random.sample(item_ids, min(6, len(item_ids)))
            p_items += [None] * (6 - len(p_items))

            cur.execute(
                """INSERT OR IGNORE INTO match_participants
                   (match_id,player_id,champion_id,team,position,
                    kills,deaths,assists,cs,damage_dealt,damage_taken,
                    gold_earned,vision_score,
                    item1_id,item2_id,item3_id,item4_id,item5_id,item6_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (match_id, pid, cid, team, position,
                 kills, deaths, assists, cs, dmg, dmg_taken,
                 gold, vision,
                 p_items[0], p_items[1], p_items[2],
                 p_items[3], p_items[4], p_items[5])
            )
            participants_inserted += 1

    print(f"  ✓ Inserted {matches_inserted} matches, {participants_inserted} participant rows")


def seed_patch_stats(conn):
    cur       = conn.cursor()
    champ_ids = [r[0] for r in cur.execute("SELECT id FROM champions").fetchall()]
    rows = []
    for cid in champ_ids:
        for patch in PATCHES:
            games = random.randint(30, 500)
            wins  = int(games * random.uniform(0.44, 0.58))
            pr    = round(random.uniform(2.0, 18.0), 2)
            br    = round(random.uniform(1.0, 10.0), 2)
            rows.append((cid, patch, games, wins, pr, br))
    conn.executemany(
        "INSERT OR IGNORE INTO champion_patch_stats (champion_id,patch,games_played,wins,pick_rate,ban_rate)"
        " VALUES (?,?,?,?,?,?)",
        rows
    )
    print(f"  ✓ Inserted {len(rows)} champion patch stat rows")


def main():
    print("\n🎮 Seeding League of Legends database...\n")
    conn = connect()

    run_schema(conn)
    seed_champions(conn)
    seed_items(conn)
    seed_players(conn)
    seed_matches(conn, n=100)
    seed_patch_stats(conn)

    conn.commit()
    conn.close()
    print(f"\n✅ Done! Database saved to: {DB_PATH}\n")


if __name__ == "__main__":
    main()
