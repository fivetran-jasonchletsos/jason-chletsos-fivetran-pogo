{{ config(materialized='table') }}

with types as (
    select * from {{ ref('stg_types') }}
),

-- Explode comma-separated damage relation strings into rows
double_damage as (
    select type_name as attacking_type, explode(split(double_damage_to, ',')) as defending_type, 2.0 as multiplier
    from types where double_damage_to != ''
),

half_damage as (
    select type_name as attacking_type, explode(split(half_damage_to, ',')) as defending_type, 0.5 as multiplier
    from types where half_damage_to != ''
),

no_damage as (
    select type_name as attacking_type, explode(split(no_damage_to, ',')) as defending_type, 0.0 as multiplier
    from types where no_damage_to != ''
),

all_types as (
    select distinct type_name from types
),

effectiveness_matrix as (
    select
        a.type_name                                                                    as attacking_type,
        d.type_name                                                                    as defending_type,
        coalesce(dd.multiplier, hd.multiplier, nd.multiplier, 1.0)                    as effectiveness_multiplier,
        case
            when nd.multiplier = 0.0 then 'No Effect'
            when hd.multiplier = 0.5 then 'Not Very Effective'
            when dd.multiplier = 2.0 then 'Super Effective'
            else 'Normal'
        end                                                                            as effectiveness_label
    from all_types a
    cross join all_types d
    left join double_damage dd on a.type_name = dd.attacking_type and d.type_name = dd.defending_type
    left join half_damage   hd on a.type_name = hd.attacking_type and d.type_name = hd.defending_type
    left join no_damage     nd on a.type_name = nd.attacking_type and d.type_name = nd.defending_type
)

select * from effectiveness_matrix
order by attacking_type, defending_type
