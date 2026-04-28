-- ================================================================
--  League of Legends Stats Database
--  queries/showcase.sql
--
--  A collection of analytical queries demonstrating:
--  JOINs, CTEs, Window Functions, Subqueries, Aggregates
-- ================================================================

-- ────────────────────────────────────────
--  Q1: Top 10 Champions by Win Rate
--      (minimum 20 games played to filter noise)
-- ────────────────────────────────────────
SELECT
    c.name                                          AS champion,
    c.primary_role                                  AS role,
    COUNT(*)                                        AS games_played,
    SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
                                                    AS wins,
    ROUND(
        100.0 * SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
        / COUNT(*), 2
    )                                               AS win_rate_pct
FROM match_participants mp
JOIN champions  c ON mp.champion_id = c.id
JOIN matches    m ON mp.match_id    = m.id
WHERE m.game_mode = 'Ranked'
GROUP BY c.id
HAVING games_played >= 20
ORDER BY win_rate_pct DESC
LIMIT 10;


-- ────────────────────────────────────────
--  Q2: Player Leaderboard — ranked by LP
--      using a window function to assign rank
-- ────────────────────────────────────────
SELECT
    RANK() OVER (ORDER BY lp DESC)  AS standing,
    summoner_name,
    region,
    rank_tier,
    COALESCE(rank_division, '')     AS division,
    lp,
    wins,
    losses,
    ROUND(100.0 * wins / NULLIF(wins + losses, 0), 1)
                                    AS winrate_pct
FROM players
ORDER BY lp DESC;


-- ────────────────────────────────────────
--  Q3: Best KDA Players (Kills+Assists / Deaths)
--      across all ranked games
-- ────────────────────────────────────────
SELECT
    p.summoner_name,
    p.rank_tier,
    COUNT(DISTINCT mp.match_id)         AS games_played,
    SUM(mp.kills)                       AS total_kills,
    SUM(mp.deaths)                      AS total_deaths,
    SUM(mp.assists)                     AS total_assists,
    ROUND(
        CAST(SUM(mp.kills) + SUM(mp.assists) AS REAL)
        / NULLIF(SUM(mp.deaths), 0), 2
    )                                   AS kda
FROM match_participants mp
JOIN players p  ON mp.player_id  = p.id
JOIN matches m  ON mp.match_id   = m.id
WHERE m.game_mode = 'Ranked'
GROUP BY p.id
HAVING games_played >= 5
ORDER BY kda DESC
LIMIT 15;


-- ────────────────────────────────────────
--  Q4: Champion Performance Per Patch
--      CTE + join to show trend over time
-- ────────────────────────────────────────
WITH patch_performance AS (
    SELECT
        c.name                      AS champion,
        m.patch,
        COUNT(*)                    AS games,
        SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
                                    AS wins,
        ROUND(
            100.0 * SUM(CASE WHEN mp.team = m.winning_team THEN 1 ELSE 0 END)
            / COUNT(*), 1
        )                           AS win_rate
    FROM match_participants mp
    JOIN champions c ON mp.champion_id = c.id
    JOIN matches   m ON mp.match_id    = m.id
    WHERE m.game_mode = 'Ranked'
    GROUP BY c.id, m.patch
)
SELECT
    champion,
    patch,
    games,
    wins,
    win_rate,
    win_rate - LAG(win_rate) OVER (PARTITION BY champion ORDER BY patch)
                                    AS win_rate_change
FROM patch_performance
ORDER BY champion, patch;


-- ────────────────────────────────────────
--  Q5: Most Popular Item Builds Per Champion
--      Finds the top 3 items built most often on each champion
-- ────────────────────────────────────────
WITH item_counts AS (
    SELECT
        c.name          AS champion,
        i.name          AS item,
        i.category,
        COUNT(*)        AS times_built
    FROM match_participants mp
    JOIN champions c ON mp.champion_id = c.id
    JOIN items     i ON i.id IN (
        mp.item1_id, mp.item2_id, mp.item3_id,
        mp.item4_id, mp.item5_id, mp.item6_id
    )
    GROUP BY c.id, i.id
),
ranked_items AS (
    SELECT
        champion,
        item,
        category,
        times_built,
        RANK() OVER (PARTITION BY champion ORDER BY times_built DESC) AS item_rank
    FROM item_counts
)
SELECT champion, item_rank, item, category, times_built
FROM ranked_items
WHERE item_rank <= 3
ORDER BY champion, item_rank;


-- ────────────────────────────────────────
--  Q6: Full Match History for a Player
--      (replace summoner name in WHERE clause)
-- ────────────────────────────────────────
SELECT
    m.game_id,
    m.patch,
    m.game_mode,
    ROUND(m.duration_secs / 60.0, 1)   AS duration_mins,
    c.name                              AS champion,
    mp.position,
    mp.kills,
    mp.deaths,
    mp.assists,
    ROUND(
        CAST(mp.kills + mp.assists AS REAL) / NULLIF(mp.deaths, 0), 2
    )                                   AS kda,
    mp.cs,
    mp.damage_dealt,
    mp.gold_earned,
    CASE WHEN mp.team = m.winning_team THEN 'WIN' ELSE 'LOSS' END
                                        AS result,
    m.played_at
FROM match_participants mp
JOIN matches   m ON mp.match_id    = m.id
JOIN champions c ON mp.champion_id = c.id
JOIN players   p ON mp.player_id   = p.id
WHERE p.summoner_name = 'CarryGod9'
ORDER BY m.played_at DESC;


-- ────────────────────────────────────────
--  Q7: Average Stats by Position
--      Useful for scouting or balance analysis
-- ────────────────────────────────────────
SELECT
    mp.position,
    ROUND(AVG(mp.kills), 2)         AS avg_kills,
    ROUND(AVG(mp.deaths), 2)        AS avg_deaths,
    ROUND(AVG(mp.assists), 2)       AS avg_assists,
    ROUND(AVG(mp.cs), 1)            AS avg_cs,
    ROUND(AVG(mp.damage_dealt))     AS avg_damage,
    ROUND(AVG(mp.vision_score), 1)  AS avg_vision,
    ROUND(AVG(mp.gold_earned))      AS avg_gold,
    COUNT(*)                        AS sample_size
FROM match_participants mp
JOIN matches m ON mp.match_id = m.id
WHERE m.game_mode = 'Ranked'
GROUP BY mp.position
ORDER BY avg_damage DESC;


-- ────────────────────────────────────────
--  Q8: Stomp Detection
--      Matches where the winner had significantly
--      higher damage than the losing team
-- ────────────────────────────────────────
WITH team_damage AS (
    SELECT
        mp.match_id,
        mp.team,
        SUM(mp.damage_dealt) AS total_damage
    FROM match_participants mp
    GROUP BY mp.match_id, mp.team
),
match_damage AS (
    SELECT
        m.game_id,
        m.patch,
        m.duration_secs,
        td1.total_damage    AS blue_damage,
        td2.total_damage    AS red_damage,
        m.winning_team,
        ABS(td1.total_damage - td2.total_damage) AS damage_gap
    FROM matches m
    JOIN team_damage td1 ON td1.match_id = m.id AND td1.team = 1
    JOIN team_damage td2 ON td2.match_id = m.id AND td2.team = 2
)
SELECT
    game_id,
    patch,
    ROUND(duration_secs / 60.0, 1)     AS duration_mins,
    blue_damage,
    red_damage,
    damage_gap,
    CASE winning_team WHEN 1 THEN 'Blue' ELSE 'Red' END AS winner
FROM match_damage
WHERE damage_gap > 50000
ORDER BY damage_gap DESC
LIMIT 10;


-- ────────────────────────────────────────
--  Q9: Champion Synergy
--      Champions that win together most often
-- ────────────────────────────────────────
SELECT
    c1.name             AS champion_1,
    c2.name             AS champion_2,
    COUNT(*)            AS games_together,
    SUM(
        CASE WHEN mp1.team = m.winning_team THEN 1 ELSE 0 END
    )                   AS wins_together,
    ROUND(
        100.0 * SUM(CASE WHEN mp1.team = m.winning_team THEN 1 ELSE 0 END)
        / COUNT(*), 1
    )                   AS win_rate_pct
FROM match_participants mp1
JOIN match_participants mp2
    ON  mp1.match_id  = mp2.match_id
    AND mp1.team      = mp2.team
    AND mp1.id        < mp2.id   -- avoid duplicate pairs
JOIN champions c1 ON mp1.champion_id = c1.id
JOIN champions c2 ON mp2.champion_id = c2.id
JOIN matches   m  ON mp1.match_id    = m.id
WHERE m.game_mode = 'Ranked'
GROUP BY c1.id, c2.id
HAVING games_together >= 5
ORDER BY win_rate_pct DESC
LIMIT 15;


-- ────────────────────────────────────────
--  Q10: Biggest Comeback Wins
--       Games where the winner had low gold
--       at 15 min (approximated by short duration
--       high-damage games)
-- ────────────────────────────────────────
WITH participant_totals AS (
    SELECT
        mp.match_id,
        mp.team,
        SUM(mp.gold_earned)     AS team_gold,
        SUM(mp.damage_dealt)    AS team_damage,
        SUM(mp.kills)           AS team_kills
    FROM match_participants mp
    GROUP BY mp.match_id, mp.team
)
SELECT
    m.game_id,
    m.patch,
    ROUND(m.duration_secs / 60.0, 1)   AS duration_mins,
    CASE m.winning_team WHEN 1 THEN 'Blue' ELSE 'Red' END   AS winner,
    winner_stats.team_gold                                   AS winner_gold,
    loser_stats.team_gold                                    AS loser_gold,
    loser_stats.team_gold - winner_stats.team_gold           AS gold_deficit_overcome
FROM matches m
JOIN participant_totals winner_stats
    ON winner_stats.match_id = m.id AND winner_stats.team = m.winning_team
JOIN participant_totals loser_stats
    ON loser_stats.match_id  = m.id AND loser_stats.team  != m.winning_team
WHERE loser_stats.team_gold > winner_stats.team_gold  -- winner had less gold
ORDER BY gold_deficit_overcome DESC
LIMIT 10;
