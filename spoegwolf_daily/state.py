# spoegwolf_daily/state.py
from __future__ import annotations
import os, json
from datetime import datetime, timedelta
from typing import Dict, Optional
import pytz

_STATE_FILE = os.getenv("STATE_FILE", "data/state.json")

def _today_za(tz_name: str) -> datetime:
    return datetime.now(pytz.timezone(tz_name))

def _date_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def _ensure_dirs():
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)

def _load() -> Dict:
    if not os.path.exists(_STATE_FILE):
        return {}
    with open(_STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save(state: Dict):
    _ensure_dirs()
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)

# spoegwolf_daily/state.py

def update_and_get_yesterday_delta(event_guid: str, today_total_included: int, tz_name: str) -> Optional[int]:
    state = _load()
    ev = state.setdefault(event_guid, {"daily": {}})
    daily = ev["daily"]

    today = _today_za(tz_name).date()
    yday = today - timedelta(days=1)
    dby  = today - timedelta(days=2)

    t_str, y_str, dby_str = today.isoformat(), yday.isoformat(), dby.isoformat()

    # Write today's snapshot only if it's not already there
    if t_str not in daily:
        daily[t_str] = int(today_total_included)
        _save(state)

    # Compute "yesterday sold" = (yesterday - day before yesterday)
    if y_str in daily and dby_str in daily:
        return int(daily[y_str]) - int(daily[dby_str])
    return None