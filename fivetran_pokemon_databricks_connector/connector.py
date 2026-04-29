"""
Pokémon GO Fivetran Connector — Databricks Edition
----------------------------------------------------
Syncs data from PokéAPI (https://pokeapi.co/api/v2/) into Databricks via the
Fivetran Connector SDK.

Tables synced (land in jason_chletsos.pokemon_raw via Fivetran):
  pokemon, pokemon_stats, pokemon_types, pokemon_abilities, pokemon_moves,
  moves, species, types

Incremental strategy: cursor on numeric ID fields per table.
"""

import time
from datetime import datetime, timezone

import requests
from fivetran_connector_sdk import Connector, Logging as log, Operations as op

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL      = "https://pokeapi.co/api/v2"
PAGE_SIZE     = 100
MAX_RETRIES   = 3
RETRY_BACKOFF = 2   # seconds, doubles each retry


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None) -> dict:
    """GET with exponential-backoff retry."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_BACKOFF * (2 ** attempt)
            log.warning(f"Request failed ({exc}), retrying in {wait}s …")
            time.sleep(wait)


def _paginate(endpoint: str) -> list[dict]:
    """Collect all resource-list items across pages."""
    results, url = [], f"{BASE_URL}/{endpoint}"
    params = {"limit": PAGE_SIZE, "offset": 0}
    while url:
        data    = _get(url, params)
        results.extend(data.get("results", []))
        url     = data.get("next")
        params  = None   # next URL already contains offset
    return results


# ---------------------------------------------------------------------------
# Schema declaration
# ---------------------------------------------------------------------------

def schema(configuration: dict):
    return [
        {
            "table": "pokemon",
            "primary_key": ["id"],
            "columns": {
                "id":              "INT",
                "name":            "STRING",
                "base_experience": "INT",
                "height":          "INT",
                "weight":          "INT",
                "is_default":      "BOOLEAN",
                "order":           "INT",
                "species_id":      "INT",
            },
        },
        {
            "table": "pokemon_stats",
            "primary_key": ["pokemon_id", "stat_name"],
            "columns": {
                "pokemon_id": "INT",
                "stat_name":  "STRING",
                "base_stat":  "INT",
                "effort":     "INT",
            },
        },
        {
            "table": "pokemon_types",
            "primary_key": ["pokemon_id", "slot"],
            "columns": {
                "pokemon_id": "INT",
                "type_name":  "STRING",
                "slot":       "INT",
            },
        },
        {
            "table": "pokemon_abilities",
            "primary_key": ["pokemon_id", "slot"],
            "columns": {
                "pokemon_id":   "INT",
                "ability_name": "STRING",
                "is_hidden":    "BOOLEAN",
                "slot":         "INT",
            },
        },
        {
            "table": "pokemon_moves",
            "primary_key": ["pokemon_id", "move_name"],
            "columns": {
                "pokemon_id": "INT",
                "move_name":  "STRING",
            },
        },
        {
            "table": "moves",
            "primary_key": ["id"],
            "columns": {
                "id":            "INT",
                "name":          "STRING",
                "accuracy":      "INT",
                "power":         "INT",
                "pp":            "INT",
                "type":          "STRING",
                "damage_class":  "STRING",
                "effect_chance": "INT",
            },
        },
        {
            "table": "species",
            "primary_key": ["id"],
            "columns": {
                "id":              "INT",
                "name":            "STRING",
                "capture_rate":    "INT",
                "base_happiness":  "INT",
                "is_legendary":    "BOOLEAN",
                "is_mythical":     "BOOLEAN",
                "generation":      "STRING",
                "habitat":         "STRING",
                "shape":           "STRING",
            },
        },
        {
            "table": "types",
            "primary_key": ["id"],
            "columns": {
                "id":                  "INT",
                "name":                "STRING",
                "double_damage_to":    "STRING",
                "half_damage_to":      "STRING",
                "no_damage_to":        "STRING",
                "double_damage_from":  "STRING",
                "half_damage_from":    "STRING",
                "no_damage_from":      "STRING",
            },
        },
    ]


# ---------------------------------------------------------------------------
# Sync helpers
# ---------------------------------------------------------------------------

def _sync_pokemon(state: dict):
    """Incremental sync of pokemon + child tables (stats, types, abilities, moves)."""
    last_id = state.get("last_pokemon_id", 0)
    all_resources = _paginate("pokemon")
    # Filter to only IDs we haven't seen yet (incremental)
    new_resources = [r for r in all_resources
                     if int(r["url"].rstrip("/").split("/")[-1]) > last_id]

    pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows = [], [], [], [], []

    for item in new_resources:
        pid  = int(item["url"].rstrip("/").split("/")[-1])
        data = _get(item["url"])

        pokemon_rows.append({
            "id":              data["id"],
            "name":            data["name"],
            "base_experience": data.get("base_experience"),
            "height":          data.get("height"),
            "weight":          data.get("weight"),
            "is_default":      data.get("is_default", True),
            "order":           data.get("order"),
            "species_id":      int(data["species"]["url"].rstrip("/").split("/")[-1])
                               if data.get("species") else None,
        })

        for stat in data.get("stats", []):
            stats_rows.append({
                "pokemon_id": data["id"],
                "stat_name":  stat["stat"]["name"],
                "base_stat":  stat["base_stat"],
                "effort":     stat["effort"],
            })

        for t in data.get("types", []):
            types_rows.append({
                "pokemon_id": data["id"],
                "type_name":  t["type"]["name"],
                "slot":       t["slot"],
            })

        for a in data.get("abilities", []):
            abilities_rows.append({
                "pokemon_id":   data["id"],
                "ability_name": a["ability"]["name"],
                "is_hidden":    a["is_hidden"],
                "slot":         a["slot"],
            })

        for m in data.get("moves", []):
            moves_rows.append({
                "pokemon_id": data["id"],
                "move_name":  m["move"]["name"],
            })

    return pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows


def _sync_moves(state: dict) -> list[dict]:
    last_id = state.get("last_move_id", 0)
    all_resources = _paginate("move")
    new_resources = [r for r in all_resources
                     if int(r["url"].rstrip("/").split("/")[-1]) > last_id]
    rows = []
    for item in new_resources:
        data = _get(item["url"])
        rows.append({
            "id":            data["id"],
            "name":          data["name"],
            "accuracy":      data.get("accuracy"),
            "power":         data.get("power"),
            "pp":            data.get("pp"),
            "type":          data["type"]["name"] if data.get("type") else None,
            "damage_class":  data["damage_class"]["name"] if data.get("damage_class") else None,
            "effect_chance": data.get("effect_chance"),
        })
    return rows


def _sync_species(state: dict) -> list[dict]:
    last_id = state.get("last_species_id", 0)
    all_resources = _paginate("pokemon-species")
    new_resources = [r for r in all_resources
                     if int(r["url"].rstrip("/").split("/")[-1]) > last_id]
    rows = []
    for item in new_resources:
        data = _get(item["url"])
        rows.append({
            "id":             data["id"],
            "name":           data["name"],
            "capture_rate":   data.get("capture_rate"),
            "base_happiness": data.get("base_happiness"),
            "is_legendary":   data.get("is_legendary", False),
            "is_mythical":    data.get("is_mythical", False),
            "generation":     data["generation"]["name"] if data.get("generation") else None,
            "habitat":        data["habitat"]["name"] if data.get("habitat") else None,
            "shape":          data["shape"]["name"] if data.get("shape") else None,
        })
    return rows


def _sync_types() -> list[dict]:
    """Types table is small (18 rows) — always full refresh."""
    all_resources = _paginate("type")
    rows = []
    for item in all_resources:
        data = _get(item["url"])
        dr   = data.get("damage_relations", {})
        rows.append({
            "id":                  data["id"],
            "name":                data["name"],
            "double_damage_to":    ",".join(t["name"] for t in dr.get("double_damage_to", [])),
            "half_damage_to":      ",".join(t["name"] for t in dr.get("half_damage_to", [])),
            "no_damage_to":        ",".join(t["name"] for t in dr.get("no_damage_to", [])),
            "double_damage_from":  ",".join(t["name"] for t in dr.get("double_damage_from", [])),
            "half_damage_from":    ",".join(t["name"] for t in dr.get("half_damage_from", [])),
            "no_damage_from":      ",".join(t["name"] for t in dr.get("no_damage_from", [])),
        })
    return rows


# ---------------------------------------------------------------------------
# Main update function
# ---------------------------------------------------------------------------

def update(configuration: dict, state: dict):
    log.info("Starting Pokémon sync to Databricks …")

    # --- Pokémon + child tables ---
    pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows = _sync_pokemon(state)

    for row in pokemon_rows:
        yield op.upsert("pokemon", row)
    log.info(f"Upserted {len(pokemon_rows)} pokemon rows")

    for row in stats_rows:
        yield op.upsert("pokemon_stats", row)
    log.info(f"Upserted {len(stats_rows)} pokemon_stats rows")

    for row in types_rows:
        yield op.upsert("pokemon_types", row)
    log.info(f"Upserted {len(types_rows)} pokemon_types rows")

    for row in abilities_rows:
        yield op.upsert("pokemon_abilities", row)
    log.info(f"Upserted {len(abilities_rows)} pokemon_abilities rows")

    for row in moves_rows:
        yield op.upsert("pokemon_moves", row)
    log.info(f"Upserted {len(moves_rows)} pokemon_moves rows")

    if pokemon_rows:
        yield op.checkpoint(state | {"last_pokemon_id": max(r["id"] for r in pokemon_rows)})

    # --- Moves ---
    move_rows = _sync_moves(state)
    for row in move_rows:
        yield op.upsert("moves", row)
    log.info(f"Upserted {len(move_rows)} moves rows")
    if move_rows:
        yield op.checkpoint(state | {"last_move_id": max(r["id"] for r in move_rows)})

    # --- Species ---
    species_rows = _sync_species(state)
    for row in species_rows:
        yield op.upsert("species", row)
    log.info(f"Upserted {len(species_rows)} species rows")
    if species_rows:
        yield op.checkpoint(state | {"last_species_id": max(r["id"] for r in species_rows)})

    # --- Types (always full refresh) ---
    type_rows = _sync_types()
    for row in type_rows:
        yield op.upsert("types", row)
    log.info(f"Upserted {len(type_rows)} types rows")

    log.info("Sync complete.")


# ---------------------------------------------------------------------------
# Connector entry point
# ---------------------------------------------------------------------------

connector = Connector(update=update, schema=schema)

if __name__ == "__main__":
    connector.debug()
