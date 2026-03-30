{{
    config(
        materialized='table',
        run_cache_freshness_tolerance='12h' if target.name == 'prod' else '7d'
    )
}}

-- stg_types is normalised: one row per (type, damage_relation, target_type).
-- We pivot here to produce an attacking × defending effectiveness matrix.
with types as (
    select * from {{ ref('stg_types') }}
),

-- All unique type names (used as both attacker and defender axes)
all_types as (
    select distinct type_name from types
),

-- Rows where the attacking type deals double damage to the defending type
double_damage as (
    select type_name as attacking_type, target_type as defending_type, 2.0 as multiplier
    from types
    where damage_relation = 'double_damage_to'
),

-- Rows where the attacking type deals half damage
half_damage as (
    select type_name as attacking_type, target_type as defending_type, 0.5 as multiplier
    from types
    where damage_relation = 'no_damage_to'
),

-- Rows where the attacking type deals no damage
no_damage as (
    select type_name as attacking_type, target_type as defending_type, 0.0 as multiplier
    from types
    where damage_relation = 'no_damage_to'
),

-- Full cross join of all type pairs, then coalesce to the known multiplier
effectiveness_matrix as (
    select
        a.type_name                                         as attacking_type,
        d.type_name                                         as defending_type,
        coalesce(dd.multiplier, hd.multiplier, nd.multiplier, 1.0) as effectiveness_multiplier,
        case
            when nd.multiplier = 0.0 then 'No Effect'
            when hd.multiplier = 0.5 then 'Not Very Effective'
            when dd.multiplier = 2.0 then 'Super Effective'
            else 'Normal'
        end                                                 as effectiveness_label
    from all_types a
    cross join all_types d
    left join double_damage dd
        on a.type_name = dd.attacking_type and d.type_name = dd.defending_type
    left join half_damage hd
        on a.type_name = hd.attacking_type and d.type_name = hd.defending_type
    left join no_damage nd
        on a.type_name = nd.attacking_type and d.type_name = nd.defending_type
)

select * from effectiveness_matrix
order by attacking_type, defending_type
