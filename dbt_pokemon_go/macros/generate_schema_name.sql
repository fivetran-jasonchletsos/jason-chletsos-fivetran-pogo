{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    
    {%- if custom_schema_name == 'pokemon_staging' -%}
        pokemon_staging
    {%- elif custom_schema_name == 'pokemon_marts' -%}
        pokemon_marts
    {%- elif custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}
