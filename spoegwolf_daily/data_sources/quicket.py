# spoegwolf_daily/data_sources/quicket.py
from __future__ import annotations
import os, time
from typing import Dict, Any, Iterable, List, Tuple, Optional
import requests
from datetime import datetime
import pytz

from ..config import CFG

BASE = "https://api.quicket.co.za"

def _headers() -> Dict[str, str]:
    api_key = CFG.get("QUICKET_API_KEY")
    usertok = CFG.get("QUICKET_USERTOKEN")
    if not api_key or not usertok:
        raise RuntimeError("Missing QUICKET_API_KEY or QUICKET_USERTOKEN in .env")
    return {
        "Accept": "application/json",
        "api_key": api_key,
        "usertoken": usertok,
        "User-Agent": "spoegwolf-daily/1.0",
    }


def _get_page(event_id: int, page: int, page_size: int = 500) -> Dict[str, Any]:
    # The API returns "pages" and "pageSize" in the envelope; typical params: page & pagesize
    url = f"{BASE}/api/events/{event_id}/guests?page={page}&pagesize={page_size}"
    r = requests.get(url, headers=_headers(), timeout=_timeouts())
    r.raise_for_status()
    return r.json()

def _safe_int_env(name: str, default: int) -> int:
    v = os.getenv(name, "")
    try:
        return int(v) if v.strip() != "" else default
    except Exception:
        return default

def _safe_float_env(name: str, default: float) -> float:
    v = os.getenv(name, "")
    try:
        return float(v) if v.strip() != "" else default
    except Exception:
        return default

def _timeouts() -> Tuple[float, float]:
    ct = _safe_float_env("REQUEST_CONNECT_TIMEOUT", 5.0)
    rt = _safe_float_env("REQUEST_READ_TIMEOUT", 15.0)
    return (ct, rt)


def iter_all_guests(event_id: int) -> Iterable[Dict[str, Any]]:
    """
    Iterate all guest rows, handling pagination with brief retries.
    """
    retries = int(os.getenv("REQUEST_RETRIES", "2"))
    page = 1
    while True:
        last_err = None
        for attempt in range(retries + 1):
            try:
                js = _get_page(event_id, page)
                break
            except requests.HTTPError as e:
                body = ""
                try:
                    body = (e.response.text or "")[:300].replace("\n", " ")
                except Exception:
                    pass
                code = getattr(e.response, "status_code", "?")
                raise RuntimeError(f"Quicket HTTP {code} for event {event_id} — {body}") from e
            except requests.RequestException as e:
                last_err = e
                if attempt < retries:
                    time.sleep(1.5 ** attempt)
                    continue
                raise RuntimeError(f"Quicket request error for event {event_id}: {e}") from e

        results = js.get("results") or []
        if not results:
            return
        for row in results:
            yield row

        pages = int(js.get("pages") or 1)
        if page >= pages:
            return
        page += 1

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def summarize_event(event_id: int, groups: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Classify by TicketType (case-insensitive exact match).
    Returns:
      {
        "adults": int,
        "kids": int,
        "total": int,       # adults + kids (excludes 'exclude')
        "excluded": int,
        "raw_total": int
      }
    """
    adults_set  = {_norm(n) for n in (groups.get("Adults") or [])}
    kids_set    = {_norm(n) for n in (groups.get("Kids") or [])}
    exclude_set = {_norm(n) for n in (groups.get("exclude") or [])}

    adults = kids = excluded = raw_total = 0

    for g in iter_all_guests(event_id):
        raw_total += 1
        if not bool(g.get("Valid", True)):
            continue

        ttype = _norm(g.get("TicketType"))
        if ttype in exclude_set:
            excluded += 1
            continue

        if ttype in adults_set:
            adults += 1
        elif ttype in kids_set:
            kids += 1
        else:
            # default bucket if unknown type (adjust to 'excluded' if you prefer)
            adults += 1

    return {
        "adults": adults,
        "kids": kids,
        "total": adults + kids,
        "excluded": excluded,
        "raw_total": raw_total,
    }

# ---- Optional: cheap event date probe (first page only) ----

def _parse_eventdate(s: str, tz_name: str) -> Optional[datetime.date]:
    if not s:
        return None
    try:
        # Example: "2025-12-18 14:00:00"
        dt_naive = datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")
        za = pytz.timezone(tz_name)
        return za.localize(dt_naive).date()
    except Exception:
        return None

def get_event_date_first_page(event_id: int, tz_name: str) -> Optional[datetime.date]:
    """
    Look at first page of guests and try to infer the earliest upcoming EventDate from TicketInformation.
    Returns a date (no time) or None.
    """
    js = _get_page(event_id, page=1, page_size=500)
    dates = []
    for row in js.get("results") or []:
        ti = row.get("TicketInformation") or {}
        d = _parse_eventdate(ti.get("EventDate"), tz_name)
        if d:
            dates.append(d)
    if not dates:
        return None
    today = datetime.now(pytz.timezone(tz_name)).date()
    upcoming = [d for d in dates if d >= today]
    return min(upcoming) if upcoming else min(dates)