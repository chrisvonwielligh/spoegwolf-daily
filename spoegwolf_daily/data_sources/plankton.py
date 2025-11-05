# spoegwolf_daily/data_sources/plankton.py
import os, time, requests
from typing import Dict, Any
from ..config import CFG

BASE = "https://plankton.mobi"

def _headers() -> Dict[str, str]:
    if not CFG["PLANKTON_AUTH"]:
        raise RuntimeError("Missing PLANKTON_AUTH in .env")
    h = {
        "Accept": "application/json",
        "Authorization": CFG["PLANKTON_AUTH"],
        "User-Agent": "spoegwolf-daily/1.0",
    }
    if CFG.get("PLANKTON_COOKIE"):
        h["Cookie"] = CFG["PLANKTON_COOKIE"]
    return h

def _timeouts():
    # tuple: (connect, read)
    ct = float(os.getenv("REQUEST_CONNECT_TIMEOUT", "5"))
    rt = float(os.getenv("REQUEST_READ_TIMEOUT", "15"))
    return (ct, rt)

def get_event_summary(event_guid: str) -> Dict[str, Any]:
    """
    GET /api/v2/events/summary/{guid}
    Fast-fail with retries + clear diagnostics.
    """
    url = f"{BASE}/api/v2/events/summary/{event_guid}"
    headers = _headers()
    retries = int(os.getenv("REQUEST_RETRIES", "2"))
    backoff = 1.5

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=_timeouts())
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            # HTTP reached but not OK — include short body preview
            body = (r.text or "")[:300].replace("\n", " ") if "r" in locals() else ""
            raise RuntimeError(
                f"Plankton [{r.status_code} {r.reason}] for {event_guid} — {body}"
            ) from e
        except requests.RequestException as e:
            # DNS/connect/read timeout, TLS issues, etc.
            last_err = e
            if attempt < retries:
                time.sleep(backoff ** attempt)
                continue
            raise RuntimeError(
                f"Plankton request error for {event_guid} at {url}: {e}"
            ) from e