#!/usr/bin/env python3
"""
run_cache_tracker.py
--------------------
Parses dbt's target/run_results.json and logs/dbt.log after each run and
appends a summary to run_cache_history.json so you can track Run Cache
savings over time.

Usage (from dbt_pokemon_go/):
    python3 ../scripts/run_cache_tracker.py            # record latest run
    python3 ../scripts/run_cache_tracker.py --report   # print full history report
    python3 ../scripts/run_cache_tracker.py --compare  # compare last two runs
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
PROJECT_DIR  = SCRIPT_DIR.parent / "dbt_pokemon_go"
RUN_RESULTS  = PROJECT_DIR / "target" / "run_results.json"
DBT_LOG      = PROJECT_DIR / "logs" / "dbt.log"
HISTORY_FILE = SCRIPT_DIR / "run_cache_history.json"

# Regex patterns for the dbt.log
_RE_SKIP     = re.compile(r'RunCache adapter: Received skip execution response for node (\S+)')
_RE_SUMMARY  = re.compile(r'Total cache hits:\s*(\d+).*?Estimated time saved:\s*([\d.]+)s.*?Freshness tolerance:\s*(\S+)', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []


def save_history(history: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def parse_log_for_cache(log_path: Path) -> dict:
    """
    Parse the dbt.log to extract Run Cache metadata:
    - which nodes were skipped
    - the official cache hit count and estimated time saved from the summary line
    """
    result = {
        "skipped_nodes":      [],
        "cache_hit_count":    0,
        "saved_time_s":       0.0,
        "freshness_tolerance": None,
        "run_cache_active":   False,
    }
    if not log_path.exists():
        return result

    # Only look at the tail of the log (last run). We read the whole file and
    # find the LAST occurrence of the summary line to handle multiple runs.
    text = log_path.read_text(errors="replace")

    if "RunCache adapter:" in text:
        result["run_cache_active"] = True

    # Collect all skip lines — take only those after the last "Run cache vX.Y.Z is enabled"
    last_enabled_pos = text.rfind("Run cache v")
    relevant_text = text[last_enabled_pos:] if last_enabled_pos != -1 else text

    result["skipped_nodes"] = _RE_SKIP.findall(relevant_text)

    # Parse the summary line (last occurrence)
    matches = list(_RE_SUMMARY.finditer(relevant_text))
    if matches:
        m = matches[-1]
        result["cache_hit_count"]    = int(m.group(1))
        result["saved_time_s"]       = float(m.group(2))
        result["freshness_tolerance"] = m.group(3)

    return result


def parse_run_results(path: Path) -> dict:
    """Parse target/run_results.json into a structured per-model summary."""
    with open(path) as f:
        raw = json.load(f)

    results         = raw.get("results", [])
    elapsed         = raw.get("elapsed_time", 0)
    generated_at    = raw.get("metadata", {}).get("generated_at", datetime.now(timezone.utc).isoformat())
    dbt_version     = raw.get("metadata", {}).get("dbt_version", "unknown")

    models = []
    for r in results:
        models.append({
            "name":           r["unique_id"].split(".")[-1],
            "status":         r.get("status", ""),
            "execution_time": round(r.get("execution_time", 0), 3),
            "message":        r.get("message", "") or "",
        })

    return {
        "generated_at":   generated_at,
        "dbt_version":    dbt_version,
        "total_elapsed_s": round(elapsed, 3),
        "models":         models,
    }


def fmt_bar(value: float, max_value: float, width: int = 40, char: str = "█") -> str:
    filled = int(round(value / max_value * width)) if max_value else 0
    return char * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_record() -> None:
    """Parse the latest run and append to history."""
    if not RUN_RESULTS.exists():
        print(f"ERROR: {RUN_RESULTS} not found. Run `dbt run` first.")
        sys.exit(1)

    rr   = parse_run_results(RUN_RESULTS)
    log  = parse_log_for_cache(DBT_LOG)

    # Build per-model cache hit flag from the skipped_nodes list
    skipped_set = set(log["skipped_nodes"])
    for m in rr["models"]:
        m["is_cache_hit"] = m["name"] in skipped_set

    executed = [m for m in rr["models"] if not m["is_cache_hit"]]

    summary = {
        "run_number":         None,   # filled below
        "recorded_at":        datetime.now(timezone.utc).isoformat(),
        "generated_at":       rr["generated_at"],
        "dbt_version":        rr["dbt_version"],
        "run_cache_active":   log["run_cache_active"],
        "freshness_tolerance": log["freshness_tolerance"],
        "total_elapsed_s":    rr["total_elapsed_s"],
        "total_models":       len(rr["models"]),
        "executed_count":     len(executed),
        "cache_hit_count":    log["cache_hit_count"],
        "saved_time_s":       log["saved_time_s"],
        "cache_hit_rate_pct": round(log["cache_hit_count"] / len(rr["models"]) * 100, 1) if rr["models"] else 0,
        "models":             rr["models"],
    }

    history = load_history()
    summary["run_number"] = len(history) + 1
    history.append(summary)
    save_history(history)

    # ---- print summary ----
    rc_badge = "✓ ACTIVE" if log["run_cache_active"] else "✗ NOT DETECTED"
    print()
    print("=" * 62)
    print(f"  Run Cache Tracker — Run #{summary['run_number']}")
    print(f"  {summary['recorded_at'][:19].replace('T', ' ')} UTC")
    print(f"  Run Cache: {rc_badge}")
    if log["freshness_tolerance"]:
        print(f"  Freshness tolerance: {log['freshness_tolerance']}")
    print("=" * 62)
    print(f"  Total models   : {summary['total_models']}")
    print(f"  Executed       : {summary['executed_count']}")
    print(f"  Cache hits     : {summary['cache_hit_count']}  ({summary['saved_time_s']}s saved)")
    print(f"  Cache hit rate : {summary['cache_hit_rate_pct']}%")
    print(f"  Total elapsed  : {summary['total_elapsed_s']}s")
    print()

    if summary["cache_hit_count"] > 0:
        print("  Models skipped by Run Cache (NO-OP):")
        for m in summary["models"]:
            if m["is_cache_hit"]:
                print(f"    ✓ {m['name']}  [{m['execution_time']}s]")
        print()
        print(f"  Compute saved  : {summary['cache_hit_rate_pct']}% of models skipped")
        print(f"  Time saved     : {summary['saved_time_s']}s")
    else:
        print("  No cache hits this run (first run or data has changed).")

    print()
    print(f"  History saved → scripts/run_cache_history.json")
    print("=" * 62)


def cmd_report() -> None:
    """Print a full history report across all recorded runs."""
    history = load_history()
    if not history:
        print("No run history found. Run `python3 run_cache_tracker.py` after a dbt run first.")
        sys.exit(0)

    print()
    print("=" * 72)
    print("  Run Cache — Historical Report")
    print("=" * 72)
    print(f"  {'Run':<5} {'Date':<20} {'Models':<8} {'Executed':<10} {'Cached':<8} {'Hit%':<7} {'Elapsed':<10} {'Saved'}")
    print("  " + "-" * 68)

    for r in history:
        rc = "✓" if r.get("run_cache_active") else " "
        print(
            f"  {rc}#{r['run_number']:<3} "
            f"{r['recorded_at'][:16].replace('T', ' '):<20} "
            f"{r['total_models']:<8} "
            f"{r['executed_count']:<10} "
            f"{r['cache_hit_count']:<8} "
            f"{r['cache_hit_rate_pct']:<6}% "
            f"{r['total_elapsed_s']:<10}s "
            f"{r['saved_time_s']}s"
        )

    print()

    total_runs   = len(history)
    total_saved  = round(sum(r["saved_time_s"] for r in history), 2)
    avg_hit_rate = round(sum(r["cache_hit_rate_pct"] for r in history) / total_runs, 1)
    best_run     = max(history, key=lambda r: r["cache_hit_rate_pct"])

    print(f"  Runs tracked       : {total_runs}")
    print(f"  Total time saved   : {total_saved}s across all runs")
    print(f"  Avg cache hit rate : {avg_hit_rate}%")
    print(f"  Best run           : #{best_run['run_number']} — {best_run['cache_hit_rate_pct']}% cache hit rate")
    print()

    # ASCII bar chart
    print("  Cache hit rate per run:")
    for r in history:
        bar = fmt_bar(r["cache_hit_rate_pct"], 100, width=40)
        rc  = "✓" if r.get("run_cache_active") else " "
        print(f"    {rc}#{r['run_number']:<3} {bar} {r['cache_hit_rate_pct']}%")

    print("=" * 72)


def cmd_compare() -> None:
    """Compare the last two runs side by side."""
    history = load_history()
    if len(history) < 2:
        print("Need at least 2 recorded runs to compare. Run dbt + tracker twice.")
        sys.exit(0)

    a, b = history[-2], history[-1]

    elapsed_delta  = round(b["total_elapsed_s"] - a["total_elapsed_s"], 3)
    executed_delta = b["executed_count"] - a["executed_count"]
    cached_delta   = b["cache_hit_count"] - a["cache_hit_count"]
    saved_delta    = round(b["saved_time_s"] - a["saved_time_s"], 3)
    rate_delta     = round(b["cache_hit_rate_pct"] - a["cache_hit_rate_pct"], 1)

    def arrow(val: float, unit: str = "", invert: bool = False) -> str:
        """invert=True means lower is better (e.g. elapsed time)."""
        if val == 0:  return f"  {val}{unit}"
        positive_is_good = (val > 0) != invert
        symbol = "▼" if val < 0 else "▲"
        colour = ""
        return f"{symbol} {abs(val)}{unit}"

    print()
    print("=" * 64)
    print(f"  Run Cache — Comparing Run #{a['run_number']} → #{b['run_number']}")
    print("=" * 64)
    print(f"  {'Metric':<28} {'Run #' + str(a['run_number']):<16} {'Run #' + str(b['run_number']):<16} Delta")
    print("  " + "-" * 60)
    print(f"  {'Run Cache active':<28} {'Yes' if a.get('run_cache_active') else 'No':<16} {'Yes' if b.get('run_cache_active') else 'No':<16}")
    print(f"  {'Total elapsed (s)':<28} {a['total_elapsed_s']:<16} {b['total_elapsed_s']:<16} {arrow(elapsed_delta, 's', invert=True)}")
    print(f"  {'Models executed':<28} {a['executed_count']:<16} {b['executed_count']:<16} {arrow(executed_delta)}")
    print(f"  {'Cache hits':<28} {a['cache_hit_count']:<16} {b['cache_hit_count']:<16} {arrow(cached_delta)}")
    print(f"  {'Cache hit rate':<28} {str(a['cache_hit_rate_pct']) + '%':<16} {str(b['cache_hit_rate_pct']) + '%':<16} {arrow(rate_delta, '%')}")
    print(f"  {'Time saved (s)':<28} {a['saved_time_s']:<16} {b['saved_time_s']:<16} {arrow(saved_delta, 's')}")
    print()

    # Models that changed status
    a_cached = {m["name"] for m in a["models"] if m.get("is_cache_hit")}
    b_cached = {m["name"] for m in b["models"] if m.get("is_cache_hit")}

    newly_cached = sorted(b_cached - a_cached)
    newly_run    = sorted(a_cached - b_cached)

    if newly_cached:
        print(f"  Newly cached in run #{b['run_number']} (Run Cache skipped these):")
        for name in newly_cached:
            print(f"    ✓ {name}")
        print()
    if newly_run:
        print(f"  Re-executed in run #{b['run_number']} (data changed):")
        for name in newly_run:
            print(f"    ↺ {name}")
        print()
    if not newly_cached and not newly_run and b["cache_hit_count"] > 0:
        print(f"  Same {b['cache_hit_count']} models cached as previous run.")

    print("=" * 64)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track Run Cache savings across dbt runs.")
    parser.add_argument("--report",  action="store_true", help="Print full history report")
    parser.add_argument("--compare", action="store_true", help="Compare last two runs")
    args = parser.parse_args()

    if args.report:
        cmd_report()
    elif args.compare:
        cmd_compare()
    else:
        cmd_record()
