{{
    config(
        materialized='table',
        run_cache_freshness_tolerance='12h' if target.name == 'prod' else '7d'
    )
}}

with pokemon_stats as (
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
    from pokemon_stats
    group by pokemon_id
),

with_totals as (
    select
        pokemon_id,
        hp,
        attack,
        defense,
        sp_attack,
        sp_defense,
        speed,
        coalesce(hp, 0)
            + coalesce(attack, 0)
            + coalesce(defense, 0)
            + coalesce(sp_attack, 0)
            + coalesce(sp_defense, 0)
            + coalesce(speed, 0) as total_base_stats
    from pivoted
),

-- Join pokemon name from stg_pokemon
final as (
    select
        p.pokemon_id,
        p.pokemon_name,
        s.hp,
        s.attack,
        s.defense,
        s.sp_attack,
        s.sp_defense,
        s.speed,
        s.total_base_stats
    from with_totals s
    inner join {{ ref('stg_pokemon') }} p
        on s.pokemon_id = p.pokemon_id
)

select * from final
