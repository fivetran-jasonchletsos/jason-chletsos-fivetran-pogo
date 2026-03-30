{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_types') }}
),

renamed as (
    select
        pokemon_id::integer as pokemon_id,
        type_name::varchar as type_name,
        slot::integer as type_slot,
        _fivetran_synced as synced_at
    from source
    where pokemon_id is not null
      and type_name is not null
)

select * from renamed
