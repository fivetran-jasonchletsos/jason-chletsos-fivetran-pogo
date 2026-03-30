{{
    config(
        materialized='table',
        run_cache_freshness_tolerance='12h' if target.name == 'prod' else '7d'
    )
}}

with moves as (
    select * from {{ ref('stg_moves') }}
),

enriched as (
    select
        move_id,
        move_name,
        move_type,
        power,
        accuracy,
        pp,
        damage_class,
        effect_chance,
        case
            when power is null then 0
            when accuracy is null then power
            else (power * accuracy / 100.0)
        end as expected_damage
    from moves
)

select * from enriched
