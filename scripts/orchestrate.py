#!/usr/bin/env python3
"""
orchestrate.py
--------------
Polls the Fivetran API for the pokemon connector and automatically triggers
`dbt run` + the run cache tracker whenever a new successful sync is detected.

Usage:
    python3 scripts/orchestrate.py            # run continuously (default)
    python3 scripts/orchestrate.py --once     # check once and exit
    python3 scripts/orchestrate.py --trigger  # force a Fivetran sync + dbt run now

Environment:
    Reads credentials from dbt_pokemon_go/.env if present.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_KEY       = "clRZSHBsOWdMMlBZU3JCMDpZUEppVHZJZVNJUFU5ekNmbWdBbVRjVjIzQzR6ZXZTTQ=="
CONNECTOR_ID  = "stricter_scarcely"
POLL_INTERVAL = 60   # seconds between status checks

REPO_ROOT   = Path(__file__).parent.parent
DBT_DIR     = REPO_ROOT / "dbt_pokemon_go"
TRACKER     = REPO_ROOT / "scripts" / "run_cache_tracker.py"
STATE_FILE  = REPO_ROOT / "scripts" / "orchestrator_state.json"

HEADERS = {
    "Authorization": f"Basic {API_KEY}",
    "Content-Type": "application/json",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)


def get_connector_status() -> dict:
    resp = requests.get(
        f"https://api.fivetran.com/v1/connectors/{CONNECTOR_ID}",
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"]


def trigger_fivetran_sync() -> None:
    log(f"Triggering Fivetran sync for connector {CONNECTOR_ID}…")
    resp = requests.post(
        f"https://api.fivetran.com/v1/connectors/{CONNECTOR_ID}/sync",
        headers=HEADERS,
        json={"force": True},
        timeout=30,
    )
    resp.raise_for_status()
    log(f"Fivetran sync triggered: {resp.json()['message']}")


def run_dbt() -> bool:
    """Run dbt and the tracker. Returns True on success."""
    log("Running dbt…")
    env = {**os.environ, "DBT_PROJECT_DIR": str(DBT_DIR)}

    result = subprocess.run(
        ["dbt", "run"],
        cwd=DBT_DIR,
        env=env,
        capture_output=False,
    )

    if result.returncode == 0:
        log("dbt run succeeded. Recording run cache stats…")
        subprocess.run(
            [sys.executable, str(TRACKER)],
            cwd=DBT_DIR,
        )
        return True
    else:
        log(f"ERROR: dbt run failed with exit code {result.returncode}")
        return False


def load_last_succeeded_at() -> str | None:
    import json
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text()).get("last_succeeded_at")
    return None


def save_last_succeeded_at(ts: str) -> None:
    import json
    STATE_FILE.write_text(json.dumps({"last_succeeded_at": ts}))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def check_and_run() -> bool:
    """
    Check if there's a new successful sync since the last recorded one.
    Returns True if dbt was triggered.
    """
    data           = get_connector_status()
    succeeded_at   = data.get("succeeded_at")
    sync_state     = data.get("status", {}).get("sync_state", "unknown")
    last_known     = load_last_succeeded_at()

    log(f"Connector status: sync_state={sync_state}, succeeded_at={succeeded_at}, last_known={last_known}")

    if not succeeded_at:
        log("No successful sync recorded yet.")
        return False

    if succeeded_at == last_known:
        log("No new sync since last dbt run. Skipping.")
        return False

    # New successful sync detected
    log(f"New sync detected! succeeded_at={succeeded_at}")
    success = run_dbt()
    if success:
        save_last_succeeded_at(succeeded_at)
    return success


def run_continuously() -> None:
    log(f"Orchestrator started. Polling every {POLL_INTERVAL}s for connector {CONNECTOR_ID}.")
    log("Press Ctrl+C to stop.")
    while True:
        try:
            check_and_run()
        except KeyboardInterrupt:
            log("Orchestrator stopped.")
            sys.exit(0)
        except Exception as exc:
            log(f"ERROR: {exc}")
        time.sleep(POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fivetran → dbt orchestrator for Pokémon GO pipeline.")
    parser.add_argument("--once",    action="store_true", help="Check once and exit")
    parser.add_argument("--trigger", action="store_true", help="Force a Fivetran sync then wait for dbt")
    args = parser.parse_args()

    if args.trigger:
        trigger_fivetran_sync()
        log(f"Waiting for sync to complete (polling every {POLL_INTERVAL}s)…")
        # Clear last known so dbt runs when sync finishes
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        run_continuously()
    elif args.once:
        check_and_run()
    else:
        run_continuously()
