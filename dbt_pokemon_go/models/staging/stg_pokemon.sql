{{
    config(
        materialized='view',
        run_cache_freshness_tolerance='24h' if target.name == 'prod' else '7d'
    )
}}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon') }}
),

renamed as (
    select
        id::integer as pokemon_id,
        name::varchar as pokemon_name,
        base_experience::integer as base_experience,
        height::integer as height_decimeters,
        weight::integer as weight_hectograms,
        is_default::boolean as is_default_form,
        "ORDER"::integer as pokedex_order,
        species_id::integer as species_id,
        _fivetran_synced as synced_at
    from source
    where id is not null
)

select * from renamed
