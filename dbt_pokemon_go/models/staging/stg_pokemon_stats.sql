{{
    config(
        materialized='view'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon_stats') }}
),

renamed as (
    select
        pokemon_id::integer as pokemon_id,
        stat_name::varchar as stat_name,
        base_stat::integer as base_stat_value,
        effort::integer as effort_value,
        _fivetran_synced as synced_at
    from source
    where pokemon_id is not null
      and stat_name is not null
)

select * from renamed
