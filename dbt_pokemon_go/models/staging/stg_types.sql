{{
    config(
        materialized='view'
    )
}}

-- The raw types table is stored in a normalised format:
-- one row per (type, damage_relation, target_type).
-- We surface it as-is and let the mart handle any pivoting.
with source as (
    select * from {{ source('pokemon_raw', 'types') }}
),

renamed as (
    select
        id::integer             as type_id,
        name::varchar           as type_name,
        damage_relation::varchar as damage_relation,
        target_type::varchar    as target_type,
        _fivetran_synced        as synced_at
    from source
    where id is not null
)

select * from renamed
