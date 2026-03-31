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
-- ============================================================


-- ============================================================
-- TILE 1a — Total Pokémon
-- Chart type: Scorecard
-- ============================================================
SELECT COUNT(*) AS total_pokemon
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON;


-- ============================================================
-- TILE 1b — Total Moves
-- Chart type: Scorecard
-- ============================================================
SELECT COUNT(*) AS total_moves
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_MOVES;


-- ============================================================
-- TILE 1c — Legendary + Mythical Count
-- Chart type: Scorecard
-- ============================================================
SELECT COUNT(*) AS legendary_and_mythical
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE is_legendary = TRUE OR is_mythical = TRUE;


-- ============================================================
-- TILE 1d — Dual-type Pokémon
-- Chart type: Scorecard
-- ============================================================
SELECT COUNT(*) AS dual_type_pokemon
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE secondary_type IS NOT NULL;


-- ============================================================
-- TILE 2 — Top 20 Attackers  (ranked by attack stat)
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: attack
-- ============================================================
SELECT
    overall_rank,
    pokemon_name,
    primary_type,
    secondary_type,
    attack,
    sp_attack,
    total_base_stats,
    tier,
    is_legendary,
    is_mythical
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TOP_ATTACKERS
WHERE overall_rank <= 20
ORDER BY overall_rank;


-- ============================================================
-- TILE 3 — Top 20 Defenders  (ranked by defense + hp)
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: combined_defensive_stat
-- ============================================================
SELECT
    overall_rank,
    pokemon_name,
    primary_type,
    secondary_type,
    hp,
    defense,
    sp_defense,
    combined_defensive_stat,
    total_base_stats,
    tier,
    is_legendary,
    is_mythical
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TOP_DEFENDERS
WHERE overall_rank <= 20
ORDER BY overall_rank;


-- ============================================================
-- TILE 4 — Pokémon Count by Primary Type
-- Chart type: Bar chart  |  X: primary_type  |  Y: pokemon_count
-- ============================================================
SELECT
    primary_type,
    COUNT(*) AS pokemon_count
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON
WHERE primary_type IS NOT NULL
GROUP BY primary_type
ORDER BY pokemon_count DESC;


-- ============================================================
-- TILE 5 — Legendary Rankings (Top 30 by total base stats)
-- Chart type: Bar chart  |  X: pokemon_name  |  Y: total_base_stats  |  Color series: rarity_tier
-- ============================================================
SELECT
    overall_rank,
    pokemon_name,
    primary_type,
    rarity_tier,
    total_base_stats,
    attack,
    defense,
    hp,
    generation
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_LEGENDARY_RANKINGS
WHERE overall_rank <= 30
ORDER BY overall_rank;


-- ============================================================
-- TILE 6 — Best Moves per Pokémon (Top 3 moves, STAB highlighted)
-- Chart type: Table
-- ============================================================
SELECT
    pokemon_name,
    primary_type,
    move_rank,
    move_name,
    move_type,
    damage_class,
    power,
    accuracy,
    expected_damage,
    is_stab
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_BEST_MOVESETS
ORDER BY expected_damage DESC, pokemon_name, move_rank
LIMIT 100;


-- ============================================================
-- TILE 7 — Type Effectiveness Heatmap
-- Chart type: Table with conditional formatting
--   (Snowsight: select Table view, apply color scale on effectiveness_multiplier)
-- ============================================================
SELECT
    attacking_type,
    defending_type,
    effectiveness_multiplier,
    effectiveness_label
FROM JASON_CHLETSOS.POKEMON_MARTS.MART_TYPE_EFFECTIVENESS
ORDER BY attacking_type, defending_type;


-- ============================================================
-- TILE 8 — Average Base Stats by Primary Type (grouped bar)
-- Chart type: Bar chart (grouped)  |  X: primary_type  |  Y: avg_base_stat  |  Series: stat_name
-- ============================================================
SELECT
    d.primary_type,
    f.stat_name,
    ROUND(AVG(f.base_stat_value), 1) AS avg_base_stat
FROM JASON_CHLETSOS.POKEMON_MARTS.FCT_POKEMON_STATS f
JOIN JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON d
    ON f.pokemon_id = d.pokemon_id
WHERE d.primary_type IS NOT NULL
  AND f.stat_name IN ('attack', 'defense', 'hp', 'speed', 'special-attack', 'special-defense')
GROUP BY d.primary_type, f.stat_name
ORDER BY d.primary_type, f.stat_name;


-- ============================================================
-- TILE 9 — Move Power Distribution by Damage Class
-- Chart type: Bar chart (grouped)  |  X: power_bucket  |  Y: move_count  |  Series: damage_class
-- ============================================================
SELECT
    damage_class,
    CASE
        WHEN power < 40  THEN '1: < 40'
        WHEN power < 60  THEN '2: 40–59'
        WHEN power < 80  THEN '3: 60–79'
        WHEN power < 100 THEN '4: 80–99'
        WHEN power < 120 THEN '5: 100–119'
        ELSE                   '6: 120+'
    END AS power_bucket,
    COUNT(*) AS move_count
FROM JASON_CHLETSOS.POKEMON_MARTS.DIM_MOVES
WHERE power IS NOT NULL
  AND damage_class IN ('physical', 'special')
GROUP BY damage_class, power_bucket
ORDER BY damage_class, power_bucket;


-- ============================================================
-- TILE 10 — Attack vs Defense Scatter (all non-legendary Pokémon)
-- Chart type: Scatter  |  X: attack  |  Y: defense  |  Size: total_base_stats
-- ============================================================
SELECT
    f.pokemon_name,
    d.primary_type,
    f.attack,
    f.defense,
    f.hp,
    f.total_base_stats
FROM JASON_CHLETSOS.POKEMON_MARTS.FCT_POKEMON_STATS f
JOIN JASON_CHLETSOS.POKEMON_MARTS.DIM_POKEMON d
    ON f.pokemon_id = d.pokemon_id
WHERE d.is_legendary = FALSE
  AND d.is_mythical  = FALSE
  AND f.attack  IS NOT NULL
  AND f.defense IS NOT NULL;
