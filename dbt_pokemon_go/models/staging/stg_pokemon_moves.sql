{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_moves') }}
),

renamed as (
    select
        pokemon_id::integer as pokemon_id,
        move_name::varchar  as move_name,
        _fivetran_synced    as synced_at
    from source
    where pokemon_id is not null
      and move_name is not null
)

select * from renamed
