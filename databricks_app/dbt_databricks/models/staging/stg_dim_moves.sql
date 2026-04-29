{{ config(materialized='view') }}

select
    move_id,
    move_name,
    move_type,
    power,
    accuracy,
    pp,
    damage_class,
    effect_chance,
    expected_damage
from {{ source('pokemon_snowflake', 'dim_moves') }}
