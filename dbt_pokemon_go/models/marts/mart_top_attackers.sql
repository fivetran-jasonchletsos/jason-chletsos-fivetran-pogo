{{
    config(
        materialized='table'
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
        ps.attack,
        ps.sp_attack,
        ps.total_base_stats,
        pd.is_legendary,
        pd.is_mythical,
        case
            when ps.attack >= 250 then 'S'
            when ps.attack >= 200 then 'A'
            when ps.attack >= 150 then 'B'
            else 'C'
        end as tier,
        row_number() over (order by ps.attack desc, ps.sp_attack desc) as overall_rank,
        row_number() over (
            partition by pd.is_legendary 
            order by ps.attack desc, ps.sp_attack desc
        ) as rank_within_legendary_status
    from pokemon_stats ps
    inner join pokemon_dim pd
        on ps.pokemon_id = pd.pokemon_id
    where ps.attack > 0
)

select * from ranked
order by overall_rank
