{{ config(materialized='table') }}

with stats as (
    select * from {{ ref('fct_pokemon_stats') }}
),

pokemon as (
    select * from {{ ref('dim_pokemon') }}
),

ranked as (
    select
        s.pokemon_id,
        s.pokemon_name,
        p.primary_type,
        p.secondary_type,
        s.attack,
        s.sp_attack,
        greatest(coalesce(s.attack, 0), coalesce(s.sp_attack, 0)) as best_attack_stat,
        s.speed,
        s.total_base_stats,
        p.is_legendary,
        p.is_mythical,
        rank() over (order by greatest(coalesce(s.attack, 0), coalesce(s.sp_attack, 0)) desc) as attack_rank
    from stats s
    left join pokemon p on s.pokemon_id = p.pokemon_id
)

select * from ranked
