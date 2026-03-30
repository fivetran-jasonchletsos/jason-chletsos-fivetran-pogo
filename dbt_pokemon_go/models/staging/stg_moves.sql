{{
    config(
        materialized='view',
        run_cache_freshness_tolerance='24h' if target.name == 'prod' else '7d'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'moves') }}
),

renamed as (
    select
        id::integer as move_id,
        name::varchar as move_name,
        accuracy::integer as accuracy,
        power::integer as power,
        pp::integer as pp,
        type::varchar as move_type,
        damage_class::varchar as damage_class,
        effect_chance::integer as effect_chance,
        _fivetran_synced as synced_at
    from source
    where id is not null
)

select * from renamed
