{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_stats') }}
),

renamed as (
    select
        pokemon_id,
        stat_name,
        base_stat   as base_stat_value,
        effort
    from source
    where pokemon_id is not null
)

select * from renamed
