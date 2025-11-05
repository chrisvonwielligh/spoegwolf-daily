#!/usr/bin/env python3
"""
Backfill one-day snapshots for specific events.
Writes/merges JSON files under data/snapshots/<event_guid>.json.

Entries to add:
- 4607d90a-e34f-4fd4-965f-fff45f528a57 : 2025-11-04 -> 5886
- df6e673e-445c-4b75-87e8-790eedc82f0e : 2025-11-04 -> 343
"""

from __future__ import annotations
import os, json

SNAP_DIR = os.getenv("SNAP_DIR", "data/snapshots")

# ---- values you asked to set ----
TO_WRITE = {
    "4607d90a-e34f-4fd4-965f-fff45f528a57": {"2025-11-04": 5886},
    "df6e673e-445c-4b75-87e8-790eedc82f0e": {"2025-11-04": 343},
}
# ---------------------------------

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def snap_path(event_guid: str) -> str:
    ensure_dir(SNAP_DIR)
    return os.path.join(SNAP_DIR, f"{event_guid}.json")

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
    changes = 0
    for guid, entries in TO_WRITE.items():
        p = snap_path(guid)
        cur = load_json(p)
        if not isinstance(cur, dict):
            cur = {}

        # merge: set only the specified dates; leave others intact
        before = json.dumps(cur, sort_keys=True)
        for d, val in entries.items():
            cur[d] = int(val)

        after = json.dumps(cur, sort_keys=True)
        if before != after:
            save_json(p, cur)
            changes += 1
            print(f"[write] {guid} -> {p} : {entries}")
        else:
            print(f"[skip]  {guid} already contains {entries}")

    print(f"Done. Files changed: {changes}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())