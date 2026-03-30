{{
    config(
        materialized='table',
        run_cache_freshness_tolerance='12h' if target.name == 'prod' else '7d'
    )
}}

with pokemon_stats as (
    select * from {{ ref('fct_pokemon_stats') }}
),

pokemon_dim as (
    select * from {{ ref('dim_pokemon') }}
),

ranked as (
    select
        ps.pokemon_id,
        ps.pokemon_name,
        pd.primary_type,
        pd.secondary_type,
        ps.hp,
        ps.defense,
        ps.sp_defense,
        ps.defense + ps.hp as combined_defensive_stat,
        ps.total_base_stats,
        pd.is_legendary,
        pd.is_mythical,
        case
            when (ps.defense + ps.hp) >= 350 then 'S'
            when (ps.defense + ps.hp) >= 300 then 'A'
            when (ps.defense + ps.hp) >= 250 then 'B'
            else 'C'
        end as tier,
        row_number() over (order by (ps.defense + ps.hp) desc) as overall_rank,
        row_number() over (
            partition by pd.is_legendary 
            order by (ps.defense + ps.hp) desc
        ) as rank_within_legendary_status
    from pokemon_stats ps
    inner join pokemon_dim pd
        on ps.pokemon_id = pd.pokemon_id
    where ps.defense > 0 and ps.hp > 0
)

select * from ranked
order by overall_rank
