{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_abilities') }}
),

renamed as (
    select
        pokemon_id::integer as pokemon_id,
        ability_name::varchar as ability_name,
        is_hidden::boolean as is_hidden_ability,
        slot::integer as ability_slot,
        _fivetran_synced as synced_at
    from source
    where pokemon_id is not null
      and ability_name is not null
)

select * from renamed
