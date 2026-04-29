{{ config(materialized='table') }}

select * from {{ ref('stg_fct_pokemon_stats') }}
