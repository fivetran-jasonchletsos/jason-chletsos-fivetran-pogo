-- ============================================================
-- Pokémon GO Analytics Dashboard — Snowflake Snowsight
-- ============================================================
-- How to use:
--   1. Open Snowsight → Dashboards → + New Dashboard
--   2. Name it "Pokémon GO Analytics"
--   3. Add a new tile for each section below (+ New Tile → From SQL)
--   4. Paste the SQL, set the chart type as noted, then click "Return to Dashboard"
--   5. Arrange tiles as desired
--
-- Context:
--   Database : JASON_CHLETSOS
--   Schemas  : POKEMON_MARTS  (tables)
--              POKEMON_STAGING (views, used for the stat radar tile)
-- ============================================================


-- ============================================================
-- TILE 1 — Scorecard row  (4 separate single-value tiles)
-- Chart type: Scorecard
-- ============================================================

-- 1a. Total Pokémon
SELECT COUNT(*) AS total_pokemon
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON;

-- 1b. Total Moves
SELECT COUNT(*) AS total_moves
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_MOVES;

-- 1c. Legendary + Mythical Count
SELECT COUNT(*) AS legendary_and_mythical
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE is_legendary OR is_mythical;

-- 1d. Dual-type Pokémon
SELECT COUNT(*) AS dual_type_pokemon
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE secondary_type IS NOT NULL;


-- ============================================================
-- TILE 2 — Top 20 Attackers
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: attacker_score
-- ============================================================
SELECT
    pokemon_name,
    primary_type,
    attack_stat,
    best_move_power,
    attacker_score,
    attacker_rank
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TOP_ATTACKERS
WHERE attacker_rank <= 20
ORDER BY attacker_rank;


-- ============================================================
-- TILE 3 — Top 20 Defenders
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: defender_score
-- ============================================================
SELECT
    pokemon_name,
    primary_type,
    defense_stat,
    stamina_stat,
    defender_score,
    defender_rank
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TOP_DEFENDERS
WHERE defender_rank <= 20
ORDER BY defender_rank;


-- ============================================================
-- TILE 4 — Pokémon Count by Primary Type
-- Chart type: Bar chart (horizontal)  |  X: pokemon_count  |  Y: primary_type
-- ============================================================
SELECT
    primary_type,
    COUNT(*) AS pokemon_count
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE primary_type IS NOT NULL
GROUP BY primary_type
ORDER BY pokemon_count DESC;


-- ============================================================
-- TILE 5 — Legendary Rankings (Top 30)
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: total_base_stats
--             Color by: is_legendary vs is_mythical
-- ============================================================
SELECT
    legendary_rank,
    pokemon_name,
    CASE
        WHEN is_mythical THEN 'Mythical'
        WHEN is_legendary THEN 'Legendary'
    END AS legendary_class,
    total_base_stats,
    primary_type
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_LEGENDARY_RANKINGS
WHERE legendary_rank <= 30
ORDER BY legendary_rank;


-- ============================================================
-- TILE 6 — Best Movesets (Top 25 by combined power)
-- Chart type: Table
-- ============================================================
SELECT
    moveset_rank,
    pokemon_name,
    primary_type,
    fast_move,
    fast_move_type,
    charged_move,
    charged_move_type,
    combined_power
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_BEST_MOVESETS
WHERE moveset_rank <= 25
ORDER BY moveset_rank;


-- ============================================================
-- TILE 7 — Type Effectiveness Heatmap
-- Chart type: Heatmap  |  X: defending_type  |  Y: attacking_type  |  Value: effectiveness_multiplier
-- (Snowsight heatmap: use Table view and apply conditional formatting if heatmap not available)
-- ============================================================
SELECT
    attacking_type,
    defending_type,
    effectiveness_multiplier,
    effectiveness_label
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TYPE_EFFECTIVENESS
ORDER BY attacking_type, defending_type;


-- ============================================================
-- TILE 8 — Average Base Stats by Type (Radar / grouped bar)
-- Chart type: Bar chart (grouped)  |  X: primary_type  |  Y: avg stat  |  Series: stat_name
-- ============================================================
SELECT
    d.primary_type,
    f.stat_name,
    ROUND(AVG(f.base_stat), 1) AS avg_base_stat
FROM JASON_CHLETSOS.POKEMON_MARTS.FCT_POKEMON_STATS f
JOIN JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON d
    ON f.pokemon_id = d.pokemon_id
WHERE d.primary_type IS NOT NULL
  AND f.stat_name IN ('attack', 'defense', 'hp', 'speed', 'special-attack', 'special-defense')
GROUP BY d.primary_type, f.stat_name
ORDER BY d.primary_type, f.stat_name;


-- ============================================================
-- TILE 9 — Move Power Distribution by Damage Class
-- Chart type: Bar chart  |  X: power_bucket  |  Y: move_count  |  Series: damage_class
-- ============================================================
SELECT
    damage_class,
    CASE
        WHEN power < 40  THEN '< 40'
        WHEN power < 60  THEN '40–59'
        WHEN power < 80  THEN '60–79'
        WHEN power < 100 THEN '80–99'
        WHEN power < 120 THEN '100–119'
        ELSE '120+'
    END AS power_bucket,
    COUNT(*) AS move_count
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_MOVES
WHERE power IS NOT NULL
  AND damage_class IN ('physical', 'special')
GROUP BY damage_class, power_bucket
ORDER BY damage_class,
    CASE power_bucket
        WHEN '< 40'   THEN 1
        WHEN '40–59'  THEN 2
        WHEN '60–79'  THEN 3
        WHEN '80–99'  THEN 4
        WHEN '100–119' THEN 5
        ELSE 6
    END;


-- ============================================================
-- TILE 10 — Attacker vs Defender Scatter (all Pokémon)
-- Chart type: Scatter  |  X: attack_stat  |  Y: defense_stat  |  Size: total_base_stats
-- ============================================================
SELECT
    d.pokemon_name,
    d.primary_type,
    MAX(CASE WHEN f.stat_name = 'attack'  THEN f.base_stat END) AS attack_stat,
    MAX(CASE WHEN f.stat_name = 'defense' THEN f.base_stat END) AS defense_stat,
    MAX(CASE WHEN f.stat_name = 'hp'      THEN f.base_stat END) AS hp_stat,
    SUM(f.base_stat) AS total_base_stats
FROM JASON_CHLETSOS.POKEMON_MARTS.FCT_POKEMON_STATS f
JOIN JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON d
    ON f.pokemon_id = d.pokemon_id
GROUP BY d.pokemon_name, d.primary_type
HAVING attack_stat IS NOT NULL AND defense_stat IS NOT NULL;
