# Pokémon GO dbt Cloud Project

A complete dbt project for transforming raw Pokémon data from PokéAPI (synced via Fivetran) into clean, battle-ready analytics tables in Snowflake.

## Project Overview

This dbt project transforms raw Pokémon data into:
- **Staging models** — Clean, typed, renamed views of raw Fivetran data
- **Dimension tables** — Denormalized Pokémon and move dimensions
- **Fact tables** — Pokémon stats pivoted into analytical format
- **Mart tables** — Business-ready views answering specific battle strategy questions

## Architecture

```
Fivetran (PokéAPI) → Snowflake (POKEMON_RAW) → dbt → Snowflake (POKEMON_STAGING, POKEMON_MARTS)
```

### Snowflake Schema Structure

- **Database**: `jason_chletsos`
- **Schemas**: `pokemon_raw`, `pokemon_staging`, `pokemon_marts`
- **Raw Schema**: `POKEMON_RAW` (Fivetran destination)
- **Staging Schema**: `POKEMON_STAGING` (dbt staging models)
- **Marts Schema**: `POKEMON_MARTS` (dbt marts models)

## Models

### Staging Models (Views in `POKEMON_STAGING`)

Clean, typed versions of raw Fivetran tables:
- `stg_pokemon` — Core Pokémon attributes
- `stg_pokemon_stats` — Individual stat values
- `stg_pokemon_types` — Type assignments
- `stg_pokemon_abilities` — Ability assignments
- `stg_pokemon_moves` — Move learnsets
- `stg_types` — Type effectiveness data
- `stg_moves` — Move details
- `stg_species` — Species-level data

### Dimension Tables (Tables in `POKEMON_MARTS`)

- **`dim_pokemon`** — Wide Pokémon dimension with types, species data, and physical attributes
- **`dim_moves`** — Enriched moves with calculated expected damage (power × accuracy)

### Fact Tables (Tables in `POKEMON_MARTS`)

- **`fct_pokemon_stats`** — Pokémon stats pivoted into columns (HP, Attack, Defense, Sp. Atk, Sp. Def, Speed) with total base stats

### Mart Tables (Tables in `POKEMON_MARTS`)

Business-ready views for battle strategy:

#### `mart_top_attackers`
**Business Question**: Which Pokémon should I use for offensive battles?

Ranks all Pokémon by Attack stat with tier classifications:
- **S Tier**: Attack ≥ 250 (Elite attackers)
- **A Tier**: Attack ≥ 200 (Strong attackers)
- **B Tier**: Attack ≥ 150 (Decent attackers)
- **C Tier**: Attack < 150 (Weak attackers)

Includes separate rankings for legendary vs non-legendary Pokémon.

#### `mart_top_defenders`
**Business Question**: Which Pokémon should I use to defend gyms?

Ranks Pokémon by combined defensive stat (Defense + HP):
- **S Tier**: Combined ≥ 350 (Elite tanks)
- **A Tier**: Combined ≥ 300 (Strong defenders)
- **B Tier**: Combined ≥ 250 (Decent defenders)
- **C Tier**: Combined < 250 (Weak defenders)

#### `mart_type_effectiveness`
**Business Question**: What types should I use against specific opponents?

Type matchup matrix showing effectiveness multipliers:
- **2.0** = Super Effective
- **1.0** = Normal damage
- **0.5** = Not Very Effective
- **0.0** = No Effect

Use this to select Pokémon with type advantage against gym defenders.

#### `mart_best_movesets`
**Business Question**: What are the best moves for each Pokémon?

Shows the top 3 most powerful moves for each Pokémon, including:
- Move power and accuracy
- Expected damage (power × accuracy / 100)
- STAB indicator (Same Type Attack Bonus — move type matches Pokémon type)
- Damage class (physical vs special)

#### `mart_legendary_rankings`
**Business Question**: Which legendary/mythical Pokémon are the strongest?

Ranks all legendary and mythical Pokémon by total base stats, separated into:
- **Legendary** tier
- **Mythical** tier

Perfect for building raid teams or prioritizing rare catches.

## Setup Instructions

### Prerequisites

1. **Snowflake account** with:
   - Database `jason_chletsos` exists
   - Schemas `pokemon_raw`, `pokemon_staging`, `pokemon_marts` created
   - Default warehouse configured
   - Role with appropriate permissions (see Snowflake setup below)

2. **Fivetran connector** deployed and syncing to `jason_chletsos.pokemon_raw`

3. **dbt Cloud account** (or dbt Core installed locally)

### Snowflake Setup

Run these commands in Snowflake to prepare the environment:

```sql
-- Use existing database
USE DATABASE jason_chletsos;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS jason_chletsos.pokemon_raw;
CREATE SCHEMA IF NOT EXISTS jason_chletsos.pokemon_staging;
CREATE SCHEMA IF NOT EXISTS jason_chletsos.pokemon_marts;

-- Create role for dbt (optional but recommended)
CREATE ROLE IF NOT EXISTS DBT_ROLE;

-- Grant permissions
GRANT USAGE ON DATABASE jason_chletsos TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT USAGE ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA jason_chletsos.pokemon_raw TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA jason_chletsos.pokemon_staging TO ROLE DBT_ROLE;
GRANT ALL ON SCHEMA jason_chletsos.pokemon_marts TO ROLE DBT_ROLE;
GRANT USAGE ON WAREHOUSE <YOUR_DEFAULT_WAREHOUSE> TO ROLE DBT_ROLE;

-- Assign role to your user
GRANT ROLE DBT_ROLE TO USER <YOUR_USERNAME>;
```

### Key Pair Authentication Setup

This project uses key pair authentication for secure Snowflake access. Your Snowflake administrator should have already generated and registered your RSA key pair.

**What you need:**
- Path to your private key file (e.g., `~/.ssh/snowflake_key.p8`)
- Private key passphrase (if your key is encrypted)

**Verify your key is registered:**
```sql
DESC USER <YOUR_USERNAME>;
-- Confirm RSA_PUBLIC_KEY_FP is present in the output
```

If you don't have a key pair configured, contact your Snowflake administrator.

### dbt Cloud Setup

#### 1. Create a new dbt Cloud project

1. Log into dbt Cloud
2. Click **"New Project"**
3. Name it `pokemon_go_dbt`

#### 2. Connect to Snowflake

1. In Project Settings → Connection, select **Snowflake**
2. Configure connection:
   - **Account**: Your Snowflake account identifier (e.g., `abc12345.us-east-1`)
   - **Role**: `DBT_ROLE` (or your custom role)
   - **Warehouse**: Your default warehouse
   - **Database**: `jason_chletsos`
   - **Schema**: `pokemon_raw` (this is the default, but models will override it)
3. Set up key pair authentication:
   - **Username**: Your Snowflake username
   - **Authentication Method**: Select **"Key Pair"**
   - **Private Key**: Upload your `snowflake_key.p8` file
   - **Private Key Passphrase**: Enter your passphrase (if you set one)
4. Click **"Test Connection"** to verify

#### 3. Connect to Git repository

1. In Project Settings → Repository, connect to your Git repo containing this dbt project
2. Set the **Project subdirectory** to `dbt_pokemon_go/` if this is part of a larger repo

#### 4. Set up environment variables

In dbt Cloud Project Settings → Environment Variables, add:
- `SNOWFLAKE_ACCOUNT` = Your Snowflake account identifier
- `SNOWFLAKE_USER` = Your Snowflake username
- `SNOWFLAKE_ROLE` = `DBT_ROLE`
- `SNOWFLAKE_WAREHOUSE` = Your default warehouse name
- `SNOWFLAKE_PRIVATE_KEY_PATH` = Path to your private key file (e.g., `/home/dbt/.ssh/snowflake_key.p8`)
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` = Passphrase for your private key (mark as secret, optional if key is unencrypted)

#### 5. Install dependencies

In the dbt Cloud IDE, run:
```bash
dbt deps
```

This installs `dbt-utils` package defined in `packages.yml`.

#### 6. Test the project

Run these commands to verify everything works:

```bash
# Compile models
dbt compile

# Run staging models only
dbt run --select staging

# Run all models
dbt run

# Run tests
dbt test
```

### Local Development (dbt Core)

If you prefer to develop locally:

1. Install dbt Core with Snowflake adapter:
```bash
pip install dbt-snowflake
```

2. Set environment variables:
```bash
export SNOWFLAKE_ACCOUNT=abc12345.us-east-1
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_ROLE=DBT_ROLE
export SNOWFLAKE_WAREHOUSE=YOUR_WAREHOUSE_NAME
export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/snowflake_key.p8
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase  # Optional if key is unencrypted
```

3. Test connection:
```bash
cd dbt_pokemon_go
dbt debug
```

4. Run models:
```bash
dbt deps
dbt run
dbt test
```

## Orchestration: Fivetran → dbt Cloud Integration

### Automatic dbt Job Triggering After Fivetran Sync

Configure Fivetran to automatically trigger your dbt Cloud job after each sync completes:

#### 1. Get dbt Cloud API credentials

1. In dbt Cloud, go to **Account Settings → API Access**
2. Create a new **Service Account Token**
3. Copy the token (you'll need this for Fivetran)
4. Note your **Account ID** and **Job ID** (found in the URL when viewing a job)

#### 2. Configure Fivetran webhook

1. In Fivetran, go to your Pokémon connector settings
2. Navigate to **Setup → Webhooks**
3. Click **"Add Webhook"**
4. Select **"dbt Cloud"** as the webhook type
5. Configure:
   - **dbt Cloud Account ID**: Your dbt Cloud account ID
   - **dbt Cloud Job ID**: Your dbt Cloud job ID
   - **API Token**: The service account token from step 1
   - **Trigger condition**: "After each sync completes successfully"
6. Click **"Test Webhook"** to verify
7. Click **"Save"**

Now, every time Fivetran syncs new Pokémon data, dbt Cloud will automatically run your transformation job.

### dbt Cloud Job Configuration

Create a production job in dbt Cloud:

1. Go to **Jobs → Create Job**
2. Configure:
   - **Job Name**: `pokemon_go_production`
   - **Environment**: Production
   - **Commands**:
     ```
     dbt deps
     dbt run
     dbt test
     ```
   - **Schedule**: Optional (since Fivetran will trigger it automatically)
     - Recommended: Daily at 2 AM as a backup
   - **Target**: `prod`
3. Save the job

### Manual Trigger

You can also manually trigger the dbt job:
- In dbt Cloud: Click **"Run Now"** on the job
- Via API: Use the dbt Cloud API to trigger the job programmatically

## Testing

The project includes comprehensive tests:

### Source Tests
- `not_null` on all primary keys
- `unique` on all primary keys
- `accepted_values` for categorical columns

### Model Tests
- Relationship tests between fact and dimension tables
- Accepted values for tier classifications (S, A, B, C)
- Accepted values for damage classes (physical, special, status)
- Accepted values for effectiveness multipliers (0.0, 0.5, 1.0, 2.0)

Run all tests:
```bash
dbt test
```

Run tests for specific models:
```bash
dbt test --select mart_top_attackers
```

## Usage Examples

### Query top 10 attackers (non-legendary)

```sql
SELECT 
    pokemon_name,
    primary_type,
    secondary_type,
    attack,
    tier
FROM jason_chletsos.pokemon_marts.MART_TOP_ATTACKERS
WHERE is_legendary = FALSE
ORDER BY overall_rank
LIMIT 10;
```

### Find best defenders against Fire-type attacks

```sql
SELECT 
    d.pokemon_name,
    d.primary_type,
    d.secondary_type,
    d.combined_defensive_stat,
    d.tier
FROM jason_chletsos.pokemon_marts.MART_TOP_DEFENDERS d
JOIN jason_chletsos.pokemon_marts.MART_TYPE_EFFECTIVENESS e
    ON d.primary_type = e.defending_type
WHERE e.attacking_type = 'fire'
    AND e.effectiveness_multiplier <= 0.5
ORDER BY d.combined_defensive_stat DESC
LIMIT 10;
```

### Get best moveset for a specific Pokémon

```sql
SELECT 
    move_name,
    move_type,
    power,
    accuracy,
    is_stab,
    move_rank
FROM jason_chletsos.pokemon_marts.MART_BEST_MOVESETS
WHERE pokemon_name = 'charizard'
ORDER BY move_rank;
```

### Compare legendary Pokémon

```sql
SELECT 
    pokemon_name,
    rarity_tier,
    total_base_stats,
    attack,
    defense,
    speed,
    overall_rank
FROM jason_chletsos.pokemon_marts.MART_LEGENDARY_RANKINGS
ORDER BY total_base_stats DESC
LIMIT 20;
```

## Maintenance

### Refreshing Reference Tables

If you need to refresh the reference tables (types, moves, species) from Fivetran:

1. In Fivetran, go to your connector settings
2. Click **"Reset"** (this will trigger a full resync)
3. Wait for the sync to complete
4. dbt Cloud will automatically run transformations via the webhook

### Adding New Models

1. Create new `.sql` file in `models/marts/` or `models/staging/`
2. Add model documentation in the corresponding `.yml` file
3. Run `dbt run --select +your_new_model` to test
4. Commit and push to Git
5. dbt Cloud will pick up the changes on the next run

### Modifying Existing Models

1. Edit the `.sql` file
2. Test locally: `dbt run --select your_model`
3. Run tests: `dbt test --select your_model`
4. Commit and push to Git
5. dbt Cloud will deploy on the next scheduled or triggered run

## Performance Optimization

### Materialization Strategy

- **Staging models**: `view` (lightweight, no storage cost)
- **Marts models**: `table` (faster queries, pre-computed)

If query performance becomes an issue, consider:
- Adding indexes in Snowflake on frequently filtered columns
- Using incremental materialization for large fact tables
- Clustering tables by commonly filtered columns

### Warehouse Sizing

The `TRANSFORMING` warehouse is set to `XSMALL` by default. This is sufficient for the Pokémon dataset (~1,000 Pokémon, ~800 moves).

If you expand the dataset or add more complex transformations, consider:
- Increasing warehouse size to `SMALL` or `MEDIUM`
- Using separate warehouses for staging vs marts
- Enabling auto-scaling

## Troubleshooting

### "Schema does not exist" error
- Verify schemas exist in Snowflake: `POKEMON_RAW`, `POKEMON_STAGING`, `POKEMON_MARTS`
- Check that your role has `USAGE` permission on these schemas

### "Relation does not exist" error
- Ensure Fivetran has completed at least one sync
- Verify tables exist in `POKEMON_RAW` schema
- Check that source definitions in `sources.yml` match actual table names

### "Compilation error" in dbt
- Run `dbt deps` to install dependencies
- Check that `profiles.yml` is correctly configured
- Verify environment variables are set

### Webhook not triggering dbt Cloud job
- Check webhook configuration in Fivetran
- Verify dbt Cloud API token is valid
- Check dbt Cloud job logs for errors
- Test webhook manually in Fivetran UI

## Project Structure

```
dbt_pokemon_go/
├── dbt_project.yml          # Project configuration
├── profiles.yml             # Snowflake connection (template)
├── packages.yml             # Dependencies (dbt-utils)
├── models/
│   ├── sources.yml          # Source definitions for Fivetran tables
│   ├── staging/
│   │   ├── staging.yml      # Staging model documentation + tests
│   │   ├── stg_pokemon.sql
│   │   ├── stg_pokemon_stats.sql
│   │   ├── stg_pokemon_types.sql
│   │   ├── stg_pokemon_abilities.sql
│   │   ├── stg_pokemon_moves.sql
│   │   ├── stg_types.sql
│   │   ├── stg_moves.sql
│   │   └── stg_species.sql
│   └── marts/
│       ├── marts.yml        # Marts documentation + tests
│       ├── dim_pokemon.sql
│       ├── dim_moves.sql
│       ├── fct_pokemon_stats.sql
│       ├── mart_top_attackers.sql
│       ├── mart_top_defenders.sql
│       ├── mart_type_effectiveness.sql
│       ├── mart_best_movesets.sql
│       └── mart_legendary_rankings.sql
└── macros/
    └── generate_schema_name.sql  # Schema routing macro
```

## Resources

- **dbt Documentation**: https://docs.getdbt.com
- **dbt Cloud**: https://cloud.getdbt.com
- **Snowflake Documentation**: https://docs.snowflake.com
- **Fivetran Documentation**: https://fivetran.com/docs
- **PokéAPI Documentation**: https://pokeapi.co/docs/v2

## Support

For issues with:
- **dbt models**: Check dbt Cloud logs and run `dbt debug`
- **Snowflake connection**: Verify credentials and permissions
- **Fivetran sync**: Check Fivetran connector logs
- **Data quality**: Run `dbt test` to identify issues

## License

This project is provided as-is for educational and analytical purposes.

Pokémon data is sourced from PokéAPI (https://pokeapi.co), which aggregates data from various Pokémon games and media.
