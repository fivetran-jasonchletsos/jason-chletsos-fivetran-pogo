# Fivetran Pokémon Connector — Databricks Edition

Custom Fivetran connector built with the [Fivetran Connector SDK](https://fivetran.com/docs/connectors/connector-sdk) that syncs Pokémon data from [PokéAPI v2](https://pokeapi.co/api/v2) directly into **Databricks Unity Catalog**.

Raw tables land in `jason_chletsos.pokemon_raw`. A dbt project in `databricks_app/dbt_databricks/` then transforms them into `jason_chletsos.pokemon_marts`, which the Streamlit app reads.

---

## Tables synced

| Table | Primary Key | Approx. rows |
|---|---|---|
| `pokemon` | `id` | 1,300+ |
| `pokemon_stats` | `pokemon_id, stat_name` | 7,800+ |
| `pokemon_types` | `pokemon_id, slot` | 2,000+ |
| `pokemon_abilities` | `pokemon_id, slot` | 3,000+ |
| `pokemon_moves` | `pokemon_id, move_name` | 300,000+ |
| `moves` | `id` | 900+ |
| `species` | `id` | 1,000+ |
| `types` | `id` | 18 |

---

## Pipeline

```
PokéAPI  →  Fivetran Connector SDK  →  jason_chletsos.pokemon_raw (Databricks)
                                              ↓
                                    dbt (databricks_app/dbt_databricks)
                                              ↓
                                    jason_chletsos.pokemon_marts (Databricks)
                                              ↓
                                    Streamlit app (ECS Fargate)
```

---

## Local development

```bash
pip install -r requirements.txt

# Debug run — writes to local warehouse.db (SQLite), not Databricks
fivetran debug .
```

---

## Deploy to Fivetran (Databricks destination)

You need:
- A base64-encoded Fivetran API key
- The Databricks destination group name in your Fivetran account

```bash
fivetran deploy . \
  --api-key <BASE64_API_KEY> \
  --destination <DATABRICKS_GROUP_NAME> \
  --connection pokemon_raw \
  --python-version 3.12
```

The `--connection` value becomes the schema name Fivetran writes to (`pokemon_raw`).
Use `--force` to update an existing connection.
