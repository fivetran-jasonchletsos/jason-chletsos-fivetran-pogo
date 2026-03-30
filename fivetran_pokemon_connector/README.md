# Fivetran Pokémon Connector

A custom Fivetran connector built with the [Fivetran Connector SDK](https://fivetran.com/docs/connectors/connector-sdk) that syncs Pokémon data from [PokéAPI v2](https://pokeapi.co/api/v2) into Snowflake.

---

## What it syncs

All tables land in the `jason_chletsos_pokemon_raw` Snowflake schema. Every row includes a `_fivetran_synced` timestamp added by Fivetran.

| Table | Primary Key | Approx. rows |
|---|---|---|
| `pokemon` | `id` | 1,300+ |
| `pokemon_stats` | `pokemon_id, stat_name` | 7,800+ |
| `pokemon_types` | `pokemon_id, slot` | 2,000+ |
| `pokemon_abilities` | `pokemon_id, slot` | 3,000+ |
| `pokemon_moves` | `pokemon_id, move_name, learn_method` | 300,000+ |
| `moves` | `id` | 900+ |
| `species` | `id` | 1,000+ |
| `types` | `id` | 18 |

---

## How it works

1. `_paginate()` walks PokéAPI list endpoints 100 records at a time, collecting resource URLs.
2. For each resource URL, `_get()` fetches the detail payload with exponential-backoff retry (3 attempts, 2s base).
3. Relevant fields are extracted and emitted as `upsert` operations keyed on the primary key — incremental syncs only touch changed rows.
4. Fivetran manages state, scheduling, and delivery to Snowflake.

---

## Configuration

`configuration.json` is the runtime config passed to the connector by Fivetran:

```json
{
  "base_url": "https://pokeapi.co/api/v2",
  "page_size": "100"
}
```

---

## Local development

```bash
pip install -r requirements.txt

# Run a local test sync (writes to a local SQLite file, not Snowflake)
python connector.py
```

To deploy changes, push to the `main` branch — Fivetran pulls from GitHub on each sync.

---

## Fivetran connection details

| Setting | Value |
|---|---|
| Connector ID | `stricter_scarcely` |
| Schema | `jason_chletsos_pokemon_raw` |
| Schedule | Every 6 hours |
| Downstream transformation | `liver_hydraulic` (triggers on sync completion) |
