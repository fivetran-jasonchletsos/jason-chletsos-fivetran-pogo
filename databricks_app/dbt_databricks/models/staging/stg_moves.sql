{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'moves') }}
),

renamed as (
    select
        id              as move_id,
        name            as move_name,
        accuracy,
        power,
        pp,
        type            as move_type,
        damage_class,
        effect_chance
    from source
    where id is not null
)

select * from renamed
