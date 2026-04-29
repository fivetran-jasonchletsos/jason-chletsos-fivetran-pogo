{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_types') }}
),

renamed as (
    select
        pokemon_id,
        type_name,
        slot        as type_slot
    from source
    where pokemon_id is not null
)

select * from renamed
