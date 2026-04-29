{{ config(materialized='table') }}

with stats as (
    select * from {{ ref('stg_pokemon_stats') }}
),

pivoted as (
    select
        pokemon_id,
        max(case when stat_name = 'hp'              then base_stat_value end) as hp,
        max(case when stat_name = 'attack'          then base_stat_value end) as attack,
        max(case when stat_name = 'defense'         then base_stat_value end) as defense,
        max(case when stat_name = 'special-attack'  then base_stat_value end) as sp_attack,
        max(case when stat_name = 'special-defense' then base_stat_value end) as sp_defense,
        max(case when stat_name = 'speed'           then base_stat_value end) as speed
    from stats
    group by pokemon_id
),

with_totals as (
    select
        p.pokemon_id,
        d.pokemon_name,
        p.hp,
        p.attack,
        p.defense,
        p.sp_attack,
        p.sp_defense,
        p.speed,
        coalesce(p.hp, 0) + coalesce(p.attack, 0) + coalesce(p.defense, 0)
            + coalesce(p.sp_attack, 0) + coalesce(p.sp_defense, 0)
            + coalesce(p.speed, 0) as total_base_stats
    from pivoted p
    left join {{ ref('dim_pokemon') }} d on p.pokemon_id = d.pokemon_id
)

select * from with_totals
