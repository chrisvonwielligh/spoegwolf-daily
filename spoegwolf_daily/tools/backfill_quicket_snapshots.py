#!/usr/bin/env python3
"""
Backfill Quicket snapshots for a specific date.
Creates/merges JSON files at: data/snapshots/quicket:<event_id>.json

Entries to add (sold on 2025-11-04):
- 342395 -> 231
- 342479 -> 200
- 344383 -> 23
"""

from __future__ import annotations
import os, json
from typing import Dict

SNAP_DIR = os.getenv("SNAP_DIR", "data/snapshots")

# --- Your backfill data (edit here if needed) ---
BACKFILL_DATE_INPUT = "2025/11/04"  # will be converted to "2025-11-04"
BACKFILL: Dict[int, int] = {
    342395: 238,
    342479: 227,
    344383: 25,
}
# -----------------------------------------------

def iso_date(s: str) -> str:
    s = (s or "").strip()
    if "/" in s:
        y, m, d = s.split("/")
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return s  # assume already ISO

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def snap_path_quicket(event_id: int) -> str:
    ensure_dir(SNAP_DIR)
    # use the same namespace key as the app: "quicket:<id>"
    fname = f"quicket:{event_id}.json"
    return os.path.join(SNAP_DIR, fname)

def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path: str, data: dict):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def main() -> int:
    date_iso = iso_date(BACKFILL_DATE_INPUT)
    changes = 0
    for eid, total in BACKFILL.items():
        p = snap_path_quicket(eid)
        cur = load_json(p)
        before = json.dumps(cur, sort_keys=True)
        cur[date_iso] = int(total)
        after = json.dumps(cur, sort_keys=True)
        if before != after:
            save_json(p, cur)
            changes += 1
            print(f"[write] quicket:{eid} {date_iso} = {total} -> {p}")
        else:
            print(f"[skip]  quicket:{eid} already has {date_iso} = {total}")
    print(f"Done. Files changed: {changes}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())