{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'species') }}
),

renamed as (
    select
        id              as species_id,
        name            as species_name,
        capture_rate,
        base_happiness,
        is_legendary,
        is_mythical,
        generation,
        habitat,
        shape           as body_shape
    from source
    where id is not null
)

select * from renamed
