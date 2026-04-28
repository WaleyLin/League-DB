-- ================================================================
--  League of Legends Stats Database
--  schema.sql — all table definitions
-- ================================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────
--  CHAMPIONS
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS champions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    title       TEXT    NOT NULL,
    class       TEXT    NOT NULL CHECK (class IN ('Assassin','Fighter','Mage','Marksman','Support','Tank')),
    primary_role TEXT   NOT NULL CHECK (primary_role IN ('Top','Jungle','Mid','Bot','Support')),
    release_year INTEGER NOT NULL,
    pick_rate   REAL    NOT NULL DEFAULT 0.0,  -- percentage e.g. 12.5 = 12.5%
    ban_rate    REAL    NOT NULL DEFAULT 0.0,
    win_rate    REAL    NOT NULL DEFAULT 50.0
);

-- ────────────────────────────────────────
--  ITEMS
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    cost        INTEGER NOT NULL,
    category    TEXT    NOT NULL CHECK (category IN ('Mythic','Legendary','Epic','Component','Starter','Boots')),
    stat_ad     INTEGER NOT NULL DEFAULT 0,   -- Attack Damage
    stat_ap     INTEGER NOT NULL DEFAULT 0,   -- Ability Power
    stat_hp     INTEGER NOT NULL DEFAULT 0,   -- Health
    stat_armor  INTEGER NOT NULL DEFAULT 0,
    stat_mr     INTEGER NOT NULL DEFAULT 0,   -- Magic Resist
    stat_as     REAL    NOT NULL DEFAULT 0.0, -- Attack Speed %
    stat_crit   INTEGER NOT NULL DEFAULT 0    -- Crit chance %
);

-- ────────────────────────────────────────
--  PLAYERS
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS players (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    summoner_name   TEXT    NOT NULL UNIQUE,
    region          TEXT    NOT NULL CHECK (region IN ('NA','EUW','EUNE','KR','BR','LAN','LAS','OCE','TR','RU','JP')),
    rank_tier       TEXT    NOT NULL CHECK (rank_tier IN ('Iron','Bronze','Silver','Gold','Platinum','Emerald','Diamond','Master','Grandmaster','Challenger')),
    rank_division   TEXT    CHECK (rank_division IN ('I','II','III','IV') OR rank_division IS NULL),
    lp              INTEGER NOT NULL DEFAULT 0,
    wins            INTEGER NOT NULL DEFAULT 0,
    losses          INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ────────────────────────────────────────
--  MATCHES
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS matches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         TEXT    NOT NULL UNIQUE,  -- e.g. NA1_1234567
    patch           TEXT    NOT NULL,         -- e.g. 14.8
    game_mode       TEXT    NOT NULL CHECK (game_mode IN ('Ranked','Normal','ARAM','URF')),
    duration_secs   INTEGER NOT NULL,         -- game length in seconds
    winning_team    INTEGER NOT NULL CHECK (winning_team IN (1,2)),  -- 1=blue, 2=red
    played_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ────────────────────────────────────────
--  MATCH PARTICIPANTS
--  One row per player per match (10 rows per match)
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS match_participants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id       INTEGER NOT NULL REFERENCES players(id),
    champion_id     INTEGER NOT NULL REFERENCES champions(id),
    team            INTEGER NOT NULL CHECK (team IN (1,2)),  -- 1=blue, 2=red
    position        TEXT    NOT NULL CHECK (position IN ('Top','Jungle','Mid','Bot','Support')),
    kills           INTEGER NOT NULL DEFAULT 0,
    deaths          INTEGER NOT NULL DEFAULT 0,
    assists         INTEGER NOT NULL DEFAULT 0,
    cs              INTEGER NOT NULL DEFAULT 0,   -- Creep Score (minions killed)
    damage_dealt    INTEGER NOT NULL DEFAULT 0,
    damage_taken    INTEGER NOT NULL DEFAULT 0,
    gold_earned     INTEGER NOT NULL DEFAULT 0,
    vision_score    INTEGER NOT NULL DEFAULT 0,
    item1_id        INTEGER REFERENCES items(id),
    item2_id        INTEGER REFERENCES items(id),
    item3_id        INTEGER REFERENCES items(id),
    item4_id        INTEGER REFERENCES items(id),
    item5_id        INTEGER REFERENCES items(id),
    item6_id        INTEGER REFERENCES items(id),
    UNIQUE (match_id, player_id)  -- a player can only appear once per match
);

-- ────────────────────────────────────────
--  CHAMPION WIN RATES PER PATCH
--  Tracks how a champion performs across different patches
-- ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS champion_patch_stats (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    champion_id  INTEGER NOT NULL REFERENCES champions(id),
    patch        TEXT    NOT NULL,
    games_played INTEGER NOT NULL DEFAULT 0,
    wins         INTEGER NOT NULL DEFAULT 0,
    pick_rate    REAL    NOT NULL DEFAULT 0.0,
    ban_rate     REAL    NOT NULL DEFAULT 0.0,
    UNIQUE (champion_id, patch)
);

-- ────────────────────────────────────────
--  INDEXES — speed up common lookups
-- ────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_participants_match   ON match_participants(match_id);
CREATE INDEX IF NOT EXISTS idx_participants_player  ON match_participants(player_id);
CREATE INDEX IF NOT EXISTS idx_participants_champ   ON match_participants(champion_id);
CREATE INDEX IF NOT EXISTS idx_matches_patch        ON matches(patch);
CREATE INDEX IF NOT EXISTS idx_matches_mode         ON matches(game_mode);
CREATE INDEX IF NOT EXISTS idx_patch_stats_champ    ON champion_patch_stats(champion_id);
