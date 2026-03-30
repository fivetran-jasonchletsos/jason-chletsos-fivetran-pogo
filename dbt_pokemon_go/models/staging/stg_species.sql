{{
    config(
        materialized='view',
        run_cache_freshness_tolerance='24h' if target.name == 'prod' else '7d'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'species') }}
),

renamed as (
    select
        id::integer as species_id,
        name::varchar as species_name,
        capture_rate::integer as capture_rate,
        base_happiness::integer as base_happiness,
        is_legendary::boolean as is_legendary,
        is_mythical::boolean as is_mythical,
        generation::varchar as generation,
        habitat::varchar as habitat,
        shape::varchar as body_shape,
        _fivetran_synced as synced_at
    from source
    where id is not null
)

select * from renamed
