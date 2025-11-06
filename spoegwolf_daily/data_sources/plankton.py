import os, time, requests
from typing import Dict, Any
from ..config import CFG

BASE = "https://plankton.mobi"

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

def _headers() -> Dict[str, str]:
    if not CFG["PLANKTON_AUTH"]:
        raise RuntimeError("Missing PLANKTON_AUTH in .env/Secrets")
    h = {
        "Accept": "application/json",
        "Authorization": CFG["PLANKTON_AUTH"],
        "User-Agent": "spoegwolf-daily/1.0",
    }
    if CFG.get("PLANKTON_COOKIE"):
        h["Cookie"] = CFG["PLANKTON_COOKIE"]
    return h

def _timeouts():
    # (connect, read)
    ct = _safe_float_env("REQUEST_CONNECT_TIMEOUT", 5.0)
    rt = _safe_float_env("REQUEST_READ_TIMEOUT", 15.0)
    return (ct, rt)

def get_event_summary(event_guid: str) -> Dict[str, Any]:
    url = f"{BASE}/api/v2/events/summary/{event_guid}"
    headers = _headers()
    retries = _safe_int_env("REQUEST_RETRIES", 2)
    backoff = 1.5

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=_timeouts())
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            body = (r.text or "")[:300].replace("\n", " ") if "r" in locals() else ""
            raise RuntimeError(
                f"Plankton [{getattr(r,'status_code', '?')} {getattr(r,'reason','?')}] at {url} — {body}"
            ) from e
        except requests.RequestException as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff ** attempt)
                continue
            raise RuntimeError(f"Plankton request error at {url}: {e}") from e