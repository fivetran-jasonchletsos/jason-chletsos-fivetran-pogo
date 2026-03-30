{{
    config(
        materialized='table'
    )
}}

with pokemon_moves as (
    select * from {{ ref('stg_pokemon_moves') }}
),

moves as (
    select * from {{ ref('dim_moves') }}
),

pokemon as (
    select * from {{ ref('dim_pokemon') }}
),

move_rankings as (
    select
        pm.pokemon_id,
        pm.move_name,
        m.move_type,
        m.power,
        m.accuracy,
        m.damage_class,
        m.expected_damage,
        row_number() over (
            partition by pm.pokemon_id 
            order by m.power desc nulls last, m.expected_damage desc
        ) as move_rank
    from pokemon_moves pm
    inner join moves m
        on pm.move_name = m.move_name
    where m.damage_class in ('physical', 'special')
      and m.power is not null
),

top_moves as (
    select
        pokemon_id,
        move_name,
        move_type,
        power,
        accuracy,
        damage_class,
        expected_damage,
        move_rank
    from move_rankings
    where move_rank <= 3
),

final as (
    select
        p.pokemon_id,
        p.pokemon_name,
        p.primary_type,
        p.secondary_type,
        tm.move_name,
        tm.move_type,
        tm.power,
        tm.accuracy,
        tm.damage_class,
        tm.expected_damage,
        tm.move_rank,
        case
            when tm.move_type = p.primary_type or tm.move_type = p.secondary_type
            then true
            else false
        end as is_stab
    from pokemon p
    inner join top_moves tm
        on p.pokemon_id = tm.pokemon_id
)

select * from final
order by pokemon_id, move_rank
