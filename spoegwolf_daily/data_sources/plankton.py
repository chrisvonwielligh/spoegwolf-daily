import requests
from typing import Dict, Any
from ..config import CFG

BASE = "https://plankton.mobi"

def _headers() -> Dict[str, str]:
    if not CFG["PLANKTON_AUTH"]:
        raise RuntimeError("Missing PLANKTON_AUTH in .env")
    h = {
        "Accept": "application/json",
        "Authorization": CFG["PLANKTON_AUTH"],
    }
    # Use cookie only if provided
    if CFG.get("PLANKTON_COOKIE"):
        h["Cookie"] = CFG["PLANKTON_COOKIE"]
    return h

def get_event_summary(event_guid: str) -> Dict[str, Any]:
    url = f"{BASE}/api/v2/events/summary/{event_guid}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()