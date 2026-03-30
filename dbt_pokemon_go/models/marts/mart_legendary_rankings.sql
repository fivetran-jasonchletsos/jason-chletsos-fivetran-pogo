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

legendary_pokemon as (
    select
        ps.pokemon_id,
        ps.pokemon_name,
        pd.primary_type,
        pd.secondary_type,
        pd.is_legendary,
        pd.is_mythical,
        pd.generation,
        ps.hp,
        ps.attack,
        ps.defense,
        ps.sp_attack,
        ps.sp_defense,
        ps.speed,
        ps.total_base_stats,
        case
            when pd.is_mythical then 'Mythical'
            when pd.is_legendary then 'Legendary'
        end as rarity_tier,
        row_number() over (order by ps.total_base_stats desc) as overall_rank,
        row_number() over (
            partition by case when pd.is_mythical then 'Mythical' else 'Legendary' end
            order by ps.total_base_stats desc
        ) as rank_within_tier
    from pokemon_stats ps
    inner join pokemon_dim pd
        on ps.pokemon_id = pd.pokemon_id
    where pd.is_legendary = true or pd.is_mythical = true
)

select * from legendary_pokemon
order by total_base_stats desc
