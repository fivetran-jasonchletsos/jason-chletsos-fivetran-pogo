{{ config(materialized='table') }}

with pokemon_moves as (
    select * from {{ ref('stg_pokemon_moves') }}
),

moves as (
    select * from {{ ref('dim_moves') }}
),

pokemon as (
    select * from {{ ref('dim_pokemon') }}
),

joined as (
    select
        pm.pokemon_id,
        p.pokemon_name,
        p.primary_type,
        p.secondary_type,
        m.move_id,
        m.move_name,
        m.move_type,
        m.power,
        m.accuracy,
        m.pp,
        m.damage_class,
        m.expected_damage,
        rank() over (
            partition by pm.pokemon_id
            order by m.expected_damage desc
        ) as move_rank_for_pokemon
    from pokemon_moves pm
    left join moves m  on pm.move_name  = m.move_name
    left join pokemon p on pm.pokemon_id = p.pokemon_id
    where m.move_id is not null
)

select * from joined
