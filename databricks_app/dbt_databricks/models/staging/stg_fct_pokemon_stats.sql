{{ config(materialized='view') }}

select
    pokemon_id,
    pokemon_name,
    hp,
    attack,
    defense,
    sp_attack,
    sp_defense,
    speed,
    total_base_stats
from {{ source('pokemon_snowflake', 'fct_pokemon_stats') }}
