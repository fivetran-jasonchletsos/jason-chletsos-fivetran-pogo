# Project Summary: jason-chletsos-fivetran-pogo

## Overview

This project is a production data pipeline that extracts Pokémon data from a public REST API,
loads it into Snowflake via a custom Fivetran connector, and transforms it into analytical
tables using dbt. The end goal is a set of Snowflake tables that answer Pokémon GO battle
strategy questions — best attackers, best defenders, optimal movesets, type matchups, and
legendary rankings.

The pipeline is fully automated: Fivetran syncs the source data on a schedule, and a native
Fivetran dbt Core transformation runs automatically after every sync with no manual steps.

---

## Technology Stack

- **Source data**: PokéAPI v2 (https://pokeapi.co/api/v2) — a free, public REST API with
  comprehensive Pokémon game data
- **Ingestion**: Fivetran Connector SDK — a Python framework for building custom Fivetran
  connectors
- **Data warehouse**: Snowflake — cloud data warehouse hosted on GCP, database `jason_chletsos`
- **Transformation**: dbt Core — SQL-based transformation framework
- **Transformation scheduling**: Fivetran native dbt Core transformation (INTEGRATED schedule)
- **Version control**: GitHub (https://github.com/fivetran-jasonchletsos/jason-chletsos-fivetran-pogo)

---

## Pipeline Flow

1. Fivetran connector `stricter_scarcely` runs on a 6-hour schedule.
2. The connector calls PokéAPI endpoints, paginates through all results (100 records per page),
   and upserts data into 8 raw tables in the `jason_chletsos_pokemon_raw` Snowflake schema.
3. On sync completion, Fivetran automatically triggers transformation `liver_hydraulic`
   (named `jason_chletsos_pogo_transformations`).
4. The transformation runs `dbt deps` (installs packages) then `dbt run` (executes all 16 models).
5. 8 staging views are created/refreshed in the `pokemon_staging` schema.
6. 8 mart tables are created/refreshed in the `pokemon_marts` schema.

---

## Fivetran Connector

**File**: `fivetran_pokemon_connector/connector.py`

The connector is built with the Fivetran Connector SDK and syncs 8 tables from PokéAPI.
It uses upsert operations keyed on primary keys so incremental syncs only update changed rows.
Retry logic handles transient API failures with exponential backoff (3 attempts).

### Tables synced into `jason_chletsos_pokemon_raw`

| Table | Primary Key | Row count (approx) |
|---|---|---|
| `pokemon` | `id` | 1,300+ |
| `pokemon_stats` | `pokemon_id, stat_name` | 7,800+ |
| `pokemon_types` | `pokemon_id, slot` | 2,000+ |
| `pokemon_abilities` | `pokemon_id, slot` | 3,000+ |
| `pokemon_moves` | `pokemon_id, move_name, learn_method` | 300,000+ |
| `moves` | `id` | 900+ |
| `species` | `id` | 1,000+ |
| `types` | `id` | 18 |

All tables include a `_fivetran_synced` timestamp column added by Fivetran.

---

## dbt Project

**Directory**: `dbt_pokemon_go/`

### Configuration

- Profile name: `twilight_expecting` (matches the Fivetran destination group ID)
- dbt version: 1.10.3 (managed by Fivetran's transformation runner)
- Package dependency: `dbt-labs/dbt_utils` v1.1.1
- Custom macro: `generate_schema_name` — ensures staging models always land in
  `pokemon_staging` and mart models always land in `pokemon_marts` regardless of
  the dbt target's default schema

### Source definitions

Defined in `models/sources.yml`. Source name: `pokemon_raw`, pointing to
`jason_chletsos.jason_chletsos_pokemon_raw`. Includes column-level descriptions and
uniqueness/not-null tests on primary key columns.

### Staging layer (`pokemon_staging` schema, materialized as views)

Staging models perform type casting, column renaming, and basic filtering.
No business logic at this layer.

| Model | Purpose |
|---|---|
| `stg_pokemon` | Casts IDs to integer, renames height/weight columns with units |
| `stg_pokemon_stats` | One row per Pokémon per stat with base_stat and effort_value |
| `stg_pokemon_types` | Type slot assignments (slot 1 = primary type) |
| `stg_pokemon_abilities` | Ability assignments with hidden ability flag |
| `stg_pokemon_moves` | Move learnsets with learn method (level-up, TM, egg, tutor) |
| `stg_moves` | Move attributes — power, accuracy, PP, type, damage class |
| `stg_species` | Species flags — is_legendary, is_mythical, capture_rate, generation |
| `stg_types` | Type damage relations — double/half/no damage target type lists |

### Mart layer (`pokemon_marts` schema, materialized as tables)

Mart models join staging models and apply business logic for Pokémon GO analytics.

| Model | Description | Key columns |
|---|---|---|
| `dim_pokemon` | Master Pokémon dimension | pokemon_id, pokemon_name, primary_type, secondary_type, is_legendary, is_mythical, total_base_stats |
| `dim_moves` | Move dimension | move_id, move_name, move_type, damage_class, power, accuracy, pp |
| `fct_pokemon_stats` | Base stats fact table | pokemon_id, stat_name, base_stat, effort_value |
| `mart_top_attackers` | Best offensive Pokémon ranked by attack + move power | pokemon_name, type, attack_stat, best_move_power, attacker_rank |
| `mart_top_defenders` | Best gym defenders ranked by defense + stamina | pokemon_name, type, defense_stat, stamina_stat, defender_score, defender_rank |
| `mart_best_movesets` | Optimal fast + charged move pairs per Pokémon | pokemon_name, fast_move, charged_move, combined_power, moveset_rank |
| `mart_legendary_rankings` | Legendary/mythical Pokémon ranked by total base stats | pokemon_name, is_legendary, is_mythical, total_base_stats, legendary_rank |
| `mart_type_effectiveness` | Full 18x18 type matchup matrix | attacking_type, defending_type, effectiveness_multiplier, effectiveness_label |

---

## Fivetran Resources

| Resource | Name / ID |
|---|---|
| Account | `jason_chletsos` (Fivetran Sales Eng Demo) |
| Destination | `jason_chletsos_snowflake_saas` (group: `twilight_expecting`) |
| Connector | `jason_chletsos_pokemon_raw` (ID: `stricter_scarcely`) |
| dbt Core project | `cheek_herald` — dbt 1.10.3, folder `dbt_pokemon_go`, branch `main` |
| Transformation | `jason_chletsos_pogo_transformations` (ID: `liver_hydraulic`) |
| Schedule | INTEGRATED — runs after every connector sync |

---

## Snowflake Configuration

| Setting | Value |
|---|---|
| Account | `A3209653506471-SALES_ENG_DEMO` |
| Database | `jason_chletsos` |
| User | `JASON.CHLETSOS@FIVETRAN.COM` |
| Role | `SALES_DEMO_ROLE` |
| Warehouse | `DEFAULT` |
| Auth method | Key pair (encrypted private key) |
| Raw schema | `jason_chletsos_pokemon_raw` |
| Staging schema | `pokemon_staging` |
| Marts schema | `pokemon_marts` |

---

## Key Design Decisions

**Why a custom connector instead of a standard Fivetran connector?**
PokéAPI is not a supported Fivetran source. The Connector SDK allows building a
fully managed connector that runs on Fivetran's infrastructure with no server to maintain.

**Why dbt Core via Fivetran instead of dbt Cloud?**
Fivetran's native dbt Core transformation runs directly against the destination using the
same credentials, requires no separate dbt Cloud account, and triggers automatically on
sync completion via the INTEGRATED schedule type.

**Why separate staging and mart schemas?**
The `generate_schema_name` macro overrides dbt's default schema concatenation behavior.
This keeps staging views and mart tables in clean, predictable schema names rather than
environment-prefixed names like `twilight_expecting_pokemon_staging`.

**Why dbt version 1.10.3?**
Fivetran's dbt Core transformation runner for Snowflake destinations does not support
dbt 1.9.x. Version 1.10.3 is the minimum supported version for this destination type.

---

## Repository Structure

```
jason-chletsos-fivetran-pogo/
├── README.md                              # Project overview and architecture
├── .gitignore
├── fivetran_pokemon_connector/
│   ├── README.md                          # Connector documentation
│   ├── connector.py                       # Connector SDK source code
│   └── configuration.json                 # Runtime configuration
└── dbt_pokemon_go/
    ├── README.md                          # dbt project documentation
    ├── dbt_project.yml                    # Project config (profile, paths, materializations)
    ├── packages.yml                       # dbt_utils dependency
    ├── profiles.yml.example               # Template for local development
    ├── requirements.txt                   # Python dependencies for local dbt runs
    ├── macros/
    │   └── generate_schema_name.sql       # Schema name override macro
    └── models/
        ├── sources.yml                    # Source table definitions and tests
        ├── staging/
        │   ├── staging.yml                # Staging model documentation
        │   ├── stg_pokemon.sql
        │   ├── stg_pokemon_stats.sql
        │   ├── stg_pokemon_types.sql
        │   ├── stg_pokemon_abilities.sql
        │   ├── stg_pokemon_moves.sql
        │   ├── stg_moves.sql
        │   ├── stg_species.sql
        │   └── stg_types.sql
        └── marts/
            ├── marts.yml                  # Mart model documentation
            ├── dim_pokemon.sql
            ├── dim_moves.sql
            ├── fct_pokemon_stats.sql
            ├── mart_top_attackers.sql
            ├── mart_top_defenders.sql
            ├── mart_best_movesets.sql
            ├── mart_legendary_rankings.sql
            └── mart_type_effectiveness.sql
```
