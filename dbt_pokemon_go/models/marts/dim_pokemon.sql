{{
    config(
        materialized='table',
        run_cache_freshness_tolerance='12h' if target.name == 'prod' else '7d'
    )
}}

with pokemon as (
    select * from {{ ref('stg_pokemon') }}
),

species as (
    select * from {{ ref('stg_species') }}
),

types as (
    select * from {{ ref('stg_pokemon_types') }}
),

-- Pivot types into primary (slot 1) and secondary (slot 2)
types_pivoted as (
    select
        pokemon_id,
        max(case when type_slot = 1 then type_name end) as primary_type,
        max(case when type_slot = 2 then type_name end) as secondary_type
    from types
    group by pokemon_id
),

final as (
    select
        p.pokemon_id,
        p.pokemon_name,
        p.base_experience,
        p.height_decimeters,
        p.weight_hectograms,
        p.is_default_form,
        p.pokedex_order,
        t.primary_type,
        t.secondary_type,
        s.species_name,
        s.capture_rate,
        s.base_happiness,
        s.is_legendary,
        s.is_mythical,
        s.generation,
        s.habitat,
        s.body_shape
    from pokemon p
    left join types_pivoted t
        on p.pokemon_id = t.pokemon_id
    left join species s
        on p.species_id = s.species_id
)

select * from final
