{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'types') }}
),

renamed as (
    select
        id              as type_id,
        name            as type_name,
        double_damage_to,
        half_damage_to,
        no_damage_to,
        double_damage_from,
        half_damage_from,
        no_damage_from
    from source
    where id is not null
)

select * from renamed
