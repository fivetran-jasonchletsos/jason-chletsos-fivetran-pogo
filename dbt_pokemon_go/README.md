# dbt Pokémon GO

dbt project that transforms raw PokéAPI data in Snowflake into Pokémon GO battle analytics.

Runs automatically via Fivetran's native dbt Core transformation (`liver_hydraulic`) after every connector sync. Can also be run locally against the same Snowflake destination.

---

## Models

### Staging layer — `pokemon_staging` schema (views)

Casts types, renames columns, and filters nulls. No business logic.

| Model | Source table |
|---|---|
| `stg_pokemon` | `pokemon` |
| `stg_pokemon_stats` | `pokemon_stats` |
| `stg_pokemon_types` | `pokemon_types` |
| `stg_pokemon_abilities` | `pokemon_abilities` |
| `stg_pokemon_moves` | `pokemon_moves` |
| `stg_moves` | `moves` |
| `stg_species` | `species` |
| `stg_types` | `types` |

### Mart layer — `pokemon_marts` schema (tables)

Joins and business logic for Pokémon GO analytics.

| Model | Description |
|---|---|
| `dim_pokemon` | Master Pokémon dimension — name, types, legendary flags, total base stats |
| `dim_moves` | Move dimension — power, accuracy, PP, type, damage class |
| `fct_pokemon_stats` | Base stats fact table — one row per Pokémon per stat |
| `mart_top_attackers` | Best offensive Pokémon ranked by attack stat + best move power |
| `mart_top_defenders` | Best gym defenders ranked by defense + stamina composite score |
| `mart_best_movesets` | Optimal fast + charged move pairs per Pokémon |
| `mart_legendary_rankings` | Legendary and mythical Pokémon ranked by total base stats |
| `mart_type_effectiveness` | Full 18×18 type matchup matrix with effectiveness multipliers |

---

## Configuration

- **Profile**: `twilight_expecting` (matches the Fivetran destination group ID — required for Fivetran's dbt runner)
- **dbt version**: 1.10.3 (managed by Fivetran; 1.9.x is not supported for Snowflake destinations)
- **Package**: `dbt-labs/dbt_utils` v1.1.1
- **Schema macro**: `macros/generate_schema_name.sql` — pins staging models to `pokemon_staging` and mart models to `pokemon_marts` regardless of the target's default schema

---

## Local development

```bash
pip install -r requirements.txt
cp profiles.yml.example profiles.yml   # fill in your Snowflake credentials
dbt deps
dbt run
dbt test
```

---

## Snowflake schemas

| Schema | Contents |
|---|---|
| `jason_chletsos_pokemon_raw` | Raw source tables written by the Fivetran connector |
| `pokemon_staging` | Staging views |
| `pokemon_marts` | Mart tables |
