# Pokémon GO / PokéAPI Fivetran Custom Connector

A production-ready Fivetran custom connector built with the Fivetran Connector SDK to sync Pokémon data from PokéAPI into Snowflake.

## Overview

This connector syncs the following tables:
- **pokemon** — Core Pokémon data (id, name, base stats, physical attributes)
- **pokemon_stats** — Individual stat values (HP, Attack, Defense, etc.)
- **pokemon_types** — Type assignments (Fire, Water, etc.)
- **pokemon_abilities** — Ability assignments with hidden ability flags
- **pokemon_moves** — Move learnsets by version and method
- **types** — Type effectiveness matrix (super effective, not very effective, immune)
- **moves** — Move details (power, accuracy, PP, damage class)
- **species** — Species-level data (legendary status, generation, habitat)

## Features

- ✅ **Incremental sync** with cursor-based state management for pokemon data
- ✅ **Exponential backoff** retry logic with rate limit handling
- ✅ **Pagination support** for large result sets
- ✅ **Error handling** with comprehensive logging
- ✅ **Configurable** via `configuration.json`
- ✅ **Local testing** via debug script

## Prerequisites

- Python 3.8+
- Fivetran account with custom connector support
- Snowflake destination configured in Fivetran

## Local Testing

### 1. Install dependencies

```bash
cd fivetran_pokemon_connector
pip install -r requirements.txt
```

### 2. Run the debug script

```bash
python debug.py
```

This will:
- Load configuration from `configuration.json`
- Execute a simulated sync
- Output all records to console
- Show schema definitions

### 3. Verify output

Check that:
- Schema is correctly defined for all 8 tables
- Records are being fetched from PokéAPI
- Pagination is working
- Incremental cursor is being updated

## Deployment to Fivetran

### Step 1: Package the connector

Create a ZIP file containing:
```
pokemon_connector.zip
├── connector.py
├── requirements.txt
└── configuration.json (optional - can be configured in UI)
```

```bash
zip -r pokemon_connector.zip connector.py requirements.txt configuration.json
```

### Step 2: Upload to Fivetran

1. Log into your Fivetran account
2. Navigate to **Connectors** → **+ Connector**
3. Search for **"Custom Connector"** or **"Python Connector"**
4. Upload `pokemon_connector.zip`
5. Configure the connector:
   - **Connector Name**: `pokemon_pokeapi`
   - **Destination**: Select your Snowflake destination
   - **Schema**: `POKEMON_RAW` (or your preferred raw schema name)

### Step 3: Configure connector settings

In the Fivetran UI, set:
- **base_url**: `https://pokeapi.co/api/v2` (default)
- **page_size**: `100` (default, can increase to 500 for faster syncs)
- **pokemon_go_json_url**: `https://raw.githubusercontent.com/pokemongo-dev-contrib/pokemongo-json-pokedex/master/output/pokemon.json`

### Step 4: Set sync frequency

Recommended: **Daily** (PokéAPI data is mostly static)

For testing: **Hourly** (but be mindful of API rate limits)

### Step 5: Run initial sync

1. Click **"Test Connection"** to verify setup
2. Click **"Start Initial Sync"**
3. Monitor the sync progress in Fivetran dashboard
4. Initial sync will take ~30-60 minutes depending on API response times

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | string | `https://pokeapi.co/api/v2` | PokéAPI base URL |
| `page_size` | integer | `100` | Number of records per API request |
| `pokemon_go_json_url` | string | GitHub URL | Pokémon GO community JSON feed |

## Incremental Sync Logic

- **pokemon** table uses cursor-based incremental sync tracking the highest `pokemon_id` processed
- Reference tables (types, moves, species) are synced once during initial sync and refreshed manually if needed
- State is persisted between syncs via Fivetran's checkpoint mechanism

## Error Handling

The connector includes:
- Exponential backoff for transient errors (network issues, timeouts)
- Rate limit detection and automatic retry with delay
- Maximum retry limit (5 attempts) before failing
- Comprehensive logging for debugging

## Monitoring

Check Fivetran logs for:
- Sync duration
- Records synced per table
- Any errors or warnings
- API rate limit warnings

## Troubleshooting

### Sync is slow
- Increase `page_size` to 500 (max supported by PokéAPI)
- PokéAPI has rate limits; the connector includes delays to respect them

### Missing records
- Check Fivetran logs for errors
- Verify PokéAPI is accessible from Fivetran's infrastructure
- Run `debug.py` locally to test data extraction

### Schema changes
- If you modify the schema in `connector.py`, you must:
  1. Re-upload the connector ZIP to Fivetran
  2. Reset the connector (this will trigger a full resync)

## Next Steps

After deploying this connector:
1. Verify data is landing in Snowflake `POKEMON_RAW` schema
2. Set up dbt Cloud project to transform the raw data (see `dbt_pokemon_go/` directory)
3. Configure Fivetran → dbt Cloud webhook for automatic transformation after each sync

## API Documentation

- PokéAPI: https://pokeapi.co/docs/v2
- Fivetran Connector SDK: https://fivetran.com/docs/connectors/connector-sdk
- Pokémon GO JSON: https://github.com/pokemongo-dev-contrib/pokemongo-json-pokedex

## Support

For issues with:
- **Connector code**: Check logs and debug locally with `debug.py`
- **Fivetran platform**: Contact Fivetran support
- **PokéAPI**: Check https://pokeapi.co status page
