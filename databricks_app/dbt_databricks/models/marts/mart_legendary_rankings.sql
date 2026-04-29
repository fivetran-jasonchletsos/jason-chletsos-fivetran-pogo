{{ config(materialized='table') }}

with pokemon as (
    select * from {{ ref('dim_pokemon') }}
),

stats as (
    select * from {{ ref('fct_pokemon_stats') }}
),

legendary as (
    select
        p.pokemon_id,
        p.pokemon_name,
        p.primary_type,
        p.secondary_type,
        p.generation,
        p.is_legendary,
        p.is_mythical,
        p.capture_rate,
        s.total_base_stats,
        s.hp,
        s.attack,
        s.defense,
        s.sp_attack,
        s.sp_defense,
        s.speed,
        rank() over (order by s.total_base_stats desc) as overall_rank
    from pokemon p
    left join stats s on p.pokemon_id = s.pokemon_id
    where p.is_legendary = true or p.is_mythical = true
)

select * from legendary
