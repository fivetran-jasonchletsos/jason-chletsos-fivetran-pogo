"""
Pokémon GO Fivetran Connector
------------------------------
Syncs data from PokéAPI (https://pokeapi.co/api/v2/) into Snowflake via the
Fivetran Connector SDK.

Tables synced:
  pokemon, pokemon_stats, pokemon_types, pokemon_abilities, pokemon_moves,
  moves, species, types

Primary keys and upsert strategy match the schema already in pokemon_raw.
"""

import time
from datetime import datetime, timezone

import requests
from fivetran_connector_sdk import Connector, Logging as log, Operations as op

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL   = "https://pokeapi.co/api/v2"
PAGE_SIZE  = 100          # PokéAPI max per page
MAX_RETRIES = 3
RETRY_BACKOFF = 2         # seconds, doubles each retry


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
            wait = RETRY_BACKOFF ** attempt
            log.warning(f"Request failed ({exc}), retrying in {wait}s…")
            time.sleep(wait)


def _paginate(endpoint: str) -> list[dict]:
    """Fetch all pages from a list endpoint and return the 'results' items."""
    url    = f"{BASE_URL}/{endpoint}?limit={PAGE_SIZE}"
    items  = []
    while url:
        data  = _get(url)
        items.extend(data.get("results", []))
        url   = data.get("next")
    return items


# ---------------------------------------------------------------------------
# Schema definition
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
                "id":             "INT",
                "name":           "STRING",
                "capture_rate":   "INT",
                "base_happiness": "INT",
                "is_legendary":   "BOOLEAN",
                "is_mythical":    "BOOLEAN",
                "generation":     "STRING",
                "habitat":        "STRING",
                "shape":          "STRING",
            },
        },
        {
            "table": "types",
            "primary_key": ["id", "damage_relation", "target_type"],
            "columns": {
                "id":              "INT",
                "name":            "STRING",
                "damage_relation": "STRING",
                "target_type":     "STRING",
            },
        },
    ]


# ---------------------------------------------------------------------------
# Sync helpers — one function per table
# ---------------------------------------------------------------------------

def _sync_pokemon(state: dict) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    """
    Fetch all pokemon and their per-pokemon child rows.
    Returns (pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows).
    """
    last_id = int(state.get("last_pokemon_id", 0))
    log.info(f"Syncing pokemon (last_id={last_id})…")

    entries = _paginate("pokemon")
    pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows = [], [], [], [], []

    for entry in entries:
        pid = int(entry["url"].rstrip("/").split("/")[-1])
        if pid <= last_id:
            continue   # already synced in a previous run

        p = _get(entry["url"])
        species_id = int(p["species"]["url"].rstrip("/").split("/")[-1]) if p.get("species") else None

        pokemon_rows.append({
            "id":              p["id"],
            "name":            p["name"],
            "base_experience": p.get("base_experience"),
            "height":          p["height"],
            "weight":          p["weight"],
            "is_default":      p["is_default"],
            "order":           p["order"],
            "species_id":      species_id,
        })

        for s in p.get("stats", []):
            stats_rows.append({
                "pokemon_id": p["id"],
                "stat_name":  s["stat"]["name"],
                "base_stat":  s["base_stat"],
                "effort":     s["effort"],
            })

        for t in p.get("types", []):
            types_rows.append({
                "pokemon_id": p["id"],
                "type_name":  t["type"]["name"],
                "slot":       t["slot"],
            })

        for a in p.get("abilities", []):
            abilities_rows.append({
                "pokemon_id":   p["id"],
                "ability_name": a["ability"]["name"],
                "is_hidden":    a["is_hidden"],
                "slot":         a["slot"],
            })

        for m in p.get("moves", []):
            moves_rows.append({
                "pokemon_id": p["id"],
                "move_name":  m["move"]["name"],
            })

        log.fine(f"  fetched pokemon #{p['id']} {p['name']}")

    return pokemon_rows, stats_rows, types_rows, abilities_rows, moves_rows


def _sync_moves(state: dict) -> list[dict]:
    last_id = int(state.get("last_move_id", 0))
    log.info(f"Syncing moves (last_id={last_id})…")

    entries = _paginate("move")
    rows = []
    for entry in entries:
        mid = int(entry["url"].rstrip("/").split("/")[-1])
        if mid <= last_id:
            continue
        m = _get(entry["url"])
        rows.append({
            "id":            m["id"],
            "name":          m["name"],
            "accuracy":      m.get("accuracy"),
            "power":         m.get("power"),
            "pp":            m.get("pp"),
            "type":          m["type"]["name"],
            "damage_class":  m["damage_class"]["name"],
            "effect_chance": m.get("effect_chance"),
        })
        log.fine(f"  fetched move #{m['id']} {m['name']}")
    return rows


def _sync_species(state: dict) -> list[dict]:
    last_id = int(state.get("last_species_id", 0))
    log.info(f"Syncing species (last_id={last_id})…")

    entries = _paginate("pokemon-species")
    rows = []
    for entry in entries:
        sid = int(entry["url"].rstrip("/").split("/")[-1])
        if sid <= last_id:
            continue
        s = _get(entry["url"])
        rows.append({
            "id":             s["id"],
            "name":           s["name"],
            "capture_rate":   s.get("capture_rate"),
            "base_happiness": s.get("base_happiness"),
            "is_legendary":   s["is_legendary"],
            "is_mythical":    s["is_mythical"],
            "generation":     s["generation"]["name"],
            "habitat":        s["habitat"]["name"] if s.get("habitat") else None,
            "shape":          s["shape"]["name"] if s.get("shape") else None,
        })
        log.fine(f"  fetched species #{s['id']} {s['name']}")
    return rows


def _sync_types() -> list[dict]:
    log.info("Syncing types…")
    entries = _paginate("type")
    rows = []
    for entry in entries:
        t = _get(entry["url"])
        for relation, targets in t["damage_relations"].items():
            for target in targets:
                rows.append({
                    "id":              t["id"],
                    "name":            t["name"],
                    "damage_relation": relation,
                    "target_type":     target["name"],
                })
    return rows


# ---------------------------------------------------------------------------
# Main update function
# ---------------------------------------------------------------------------

def update(configuration: dict, state: dict):
    log.info("Starting Pokémon GO connector sync…")

    # --- Pokemon + child tables ---
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

    # Save pokemon cursor
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

    # --- Types (small table, always full refresh) ---
    type_rows = _sync_types()
    for row in type_rows:
        yield op.upsert("types", row)
    log.info(f"Upserted {len(type_rows)} types rows")

    log.info("Sync complete.")


# ---------------------------------------------------------------------------
# Connector entry point
# ---------------------------------------------------------------------------

connector = Connector(update=update, schema=schema)

