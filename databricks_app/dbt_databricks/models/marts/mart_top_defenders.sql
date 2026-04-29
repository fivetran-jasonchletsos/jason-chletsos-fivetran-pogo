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
        s.defense,
        s.sp_defense,
        greatest(coalesce(s.defense, 0), coalesce(s.sp_defense, 0)) as best_defense_stat,
        s.hp,
        s.total_base_stats,
        p.is_legendary,
        p.is_mythical,
        rank() over (order by greatest(coalesce(s.defense, 0), coalesce(s.sp_defense, 0)) desc) as defense_rank
    from stats s
    left join pokemon p on s.pokemon_id = p.pokemon_id
)

select * from ranked
