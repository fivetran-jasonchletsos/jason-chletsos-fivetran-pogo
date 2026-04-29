{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_moves') }}
),

renamed as (
    select
        pokemon_id,
        move_name
    from source
    where pokemon_id is not null
      and move_name is not null
)

select * from renamed
