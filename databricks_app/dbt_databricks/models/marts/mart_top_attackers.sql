{{ config(materialized='table') }}

select * from {{ source('pokemon_snowflake', 'mart_top_attackers') }}
