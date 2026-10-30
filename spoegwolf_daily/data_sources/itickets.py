from __future__ import annotations

import csv
import io
import re
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


def _type_matches(ticket_type: str, pattern: str) -> bool:
    """Case-insensitive; a number won't match inside a bigger number ("17" not in "R170")."""
    rx = r"(?<!\d)" + re.escape(pattern.strip()) + r"(?!\d)"
    return re.search(rx, ticket_type or "", re.IGNORECASE) is not None


def summarize_itickets_total(
    rows: List[Dict[str, Any]],
    groups: Dict[str, List[str]] | None = None,
) -> Dict[str, Any]:
    # groups: optional {"17 DEC": ["17"], ...}. A row goes to the first group with a
    # pattern found in its `type`; non-matching rows are counted in "other".
    def is_void(r: Dict[str, Any]) -> bool:
        return (r.get("VOID") or "").strip() == "1"

    def is_vip(r: Dict[str, Any]) -> bool:
        return (r.get("type") or "").strip().lower() == "vip"

    normal = 0
    vip = 0

    group_counts = {label: 0 for label in (groups or {})}
    other = 0

    for r in rows:
        if is_void(r):
            continue
        if groups:
            t = r.get("type") or ""
            for label, patterns in groups.items():
                if any(_type_matches(t, p) for p in patterns):
                    group_counts[label] += 1
                    break
            else:
                other += 1
        if is_vip(r):
            vip += 1
        else:
            normal += 1

    return {
        "normal": int(normal),
        "vip": int(vip),
        "total_sold": int(normal + vip),
        "groups": group_counts,
        "other": other,
    }


if __name__ == "__main__":
    # List ticket types in a feed:
    #   python -m spoegwolf_daily.data_sources.itickets ITICKETS_FEED_STILBAAI
    import sys
    from collections import Counter
    from dotenv import load_dotenv

    load_dotenv()
    rows = fetch_itickets_csv_via_curl(os.environ[sys.argv[1]])
    print("columns:", list(rows[0].keys()) if rows else "(no rows)")
    for t, n in Counter((r.get("type") or "").strip() for r in rows).most_common():
        print(f"{n:6}  {t!r}")