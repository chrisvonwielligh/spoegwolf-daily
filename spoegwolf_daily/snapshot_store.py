from __future__ import annotations
import os, json
from datetime import datetime, timedelta
from typing import Dict, Optional
import pytz

SNAP_DIR = os.getenv("SNAP_DIR", "data/snapshots")

def _ensure_dir():
    os.makedirs(SNAP_DIR, exist_ok=True)

def _snap_path(event_guid: str) -> str:
    _ensure_dir()
    return os.path.join(SNAP_DIR, f"{event_guid}.json")

def load_snapshots(event_guid: str) -> Dict[str, int]:
    p = _snap_path(event_guid)
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_snapshot(event_guid: str, date_str: str, total: int) -> bool:
    """
    Add/overwrite the value for date_str. Returns True if file changed.
    Meant for the nightly job only.
    """
    snaps = load_snapshots(event_guid)
    before = snaps.get(date_str)
    snaps[date_str] = int(total)
    changed = (before != snaps[date_str])
    if changed:
        with open(_snap_path(event_guid), "w", encoding="utf-8") as f:
            json.dump(snaps, f, indent=2, sort_keys=True)
    return changed

def yesterday_delta(event_guid: str, tz_name: str) -> Optional[int]:
    """
    Delta = snapshots[yesterday] - snapshots[day_before_yesterday]
    Returns None if either is missing.
    """
    snaps = load_snapshots(event_guid)
    tz = pytz.timezone(tz_name)
    today = datetime.now(tz).date()
    y = (today - timedelta(days=1)).isoformat()
    dby = (today - timedelta(days=2)).isoformat()
    if y in snaps and dby in snaps:
        return int(snaps[y]) - int(snaps[dby])
    return None