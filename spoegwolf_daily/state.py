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

def update_and_get_yesterday_delta(event_guid: str, today_total_included: int, tz_name: str) -> Optional[int]:
    """
    Store today's included total for this event and return:
      (yesterday_total - day_before_yesterday_total)
    Returns None if there isn't enough history yet.
    """
    state = _load()
    ev = state.setdefault(event_guid, {"daily": {}})
    daily = ev["daily"]

    today = _today_za(tz_name).date()
    yday = today - timedelta(days=1)
    dby  = today - timedelta(days=2)

    t_str   = today.isoformat()
    y_str   = yday.isoformat()
    dby_str = dby.isoformat()

    # Always record today's snapshot (idempotent)
    daily[t_str] = int(today_total_included)

    # Compute delta if we have both yesterday and day-before
    if y_str in daily and dby_str in daily:
        delta = int(daily[y_str]) - int(daily[dby_str])
    else:
        delta = None

    _save(state)
    return delta