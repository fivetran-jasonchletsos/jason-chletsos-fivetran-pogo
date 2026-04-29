{{ config(materialized='view') }}

with source as (
    select * from {{ source('pokemon_raw', 'pokemon') }}
),

renamed as (
    select
        id              as pokemon_id,
        name            as pokemon_name,
        base_experience,
        height          as height_decimeters,
        weight          as weight_hectograms,
        is_default      as is_default_form,
        `order`         as pokedex_order,
        species_id
    from source
    where id is not null
)

select * from renamed
