from __future__ import annotations

import csv
import io
import os
import subprocess
from typing import Dict, Any, List


def fetch_itickets_csv_via_curl(url: str) -> List[Dict[str, Any]]:
    proc = subprocess.run(
        ["curl", "-sSL", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed (rc={proc.returncode}): {proc.stderr.strip()}")

    text = proc.stdout.strip()
    if not text:
        return []

    first = text.splitlines()[0].strip().lower()
    if first == "key":
        raise RuntimeError("iTickets returned 'key' (request rejected / invalid key).")

    reader = csv.DictReader(io.StringIO(proc.stdout))
    return list(reader)


def summarize_itickets_total(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def is_void(r: Dict[str, Any]) -> bool:
        return (r.get("VOID") or "").strip() == "1"

    def is_vip(r: Dict[str, Any]) -> bool:
        return (r.get("type") or "").strip().lower() == "vip"

    normal = 0
    vip = 0

    for r in rows:
        if is_void(r):
            continue
        if is_vip(r):
            vip += 1
        else:
            normal += 1

    return {
        "normal": int(normal),
        "vip": int(vip),
        "total_sold": int(normal + vip),
    }