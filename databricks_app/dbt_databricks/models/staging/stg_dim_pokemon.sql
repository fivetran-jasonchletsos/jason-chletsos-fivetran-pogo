-- Staging pass-through for dim_pokemon from Snowflake source catalog
{{ config(materialized='view') }}

select
    pokemon_id,
    pokemon_name,
    base_experience,
    height_decimeters,
    weight_hectograms,
    is_default_form,
    pokedex_order,
    primary_type,
    secondary_type,
    species_name,
    capture_rate,
    base_happiness,
    is_legendary,
    is_mythical,
    generation,
    habitat,
    body_shape
from {{ source('pokemon_snowflake', 'dim_pokemon') }}
