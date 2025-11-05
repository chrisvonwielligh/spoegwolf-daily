# spoegwolf_daily/main.py

from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any, Optional
import pytz

from .config import CFG, SHOWS, QUICKET_EVENTS
from .data_sources.plankton import get_event_summary
from .data_sources.quicket import (
    summarize_event as quicket_summarize,
    get_event_date_first_page,
)
from .data_sources.shopify import get_shopify_last7_summary
from .summarize_af import build_message
from .senders.emailer import send_email_summary
from .snapshot_store import yesterday_delta


# ---------- helpers ----------
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _sum_by_names(ticket_info: List[Dict[str, Any]], wanted_names: Optional[List[str]]) -> int:
    """Plankton helper: sum ticketsIssued for specific ticketName strings (case-insensitive)."""
    if not ticket_info or not wanted_names:
        return 0
    wanted = {_norm(n) for n in wanted_names}
    total = 0
    for t in ticket_info:
        name = _norm(t.get("ticketName"))
        if name in wanted:
            total += int(t.get("ticketsIssued") or 0)
    return total

def _days_to_event_from_eventdate(eventdate_iso: Optional[str], tz_name: str) -> Optional[int]:
    """Plankton EventDate: 'YYYY-MM-DDTHH:MM:SS' -> days remaining."""
    if not eventdate_iso:
        return None
    try:
        # Plankton sample: "2026-01-31T10:15:00"
        dt_naive = datetime.strptime(eventdate_iso.strip(), "%Y-%m-%dT%H:%M:%S")
        tz = pytz.timezone(tz_name)
        d = tz.localize(dt_naive).date()
        today = datetime.now(tz).date()
        return (d - today).days
    except Exception:
        return None

def _days_to(date_obj, tz_name: str) -> Optional[int]:
    if not date_obj:
        return None
    today = datetime.now(pytz.timezone(tz_name)).date()
    return (date_obj - today).days
# --------------------------------


def generate_summary_text() -> str:
    """
    Build the full summary without sending email.
    Read-only: uses snapshots for 'Gister se verkope'.
    """
    tz = CFG["TZ"]

    # -------- Plankton blocks --------
    blocks = []
    for show in SHOWS:
        js = get_event_summary(show["event_guid"])
        tinfo = js.get("TicketInfo", [])

        groups = show.get("groups", {})
        ga   = _sum_by_names(tinfo, groups.get("GA (Adults)"))
        kids = _sum_by_names(tinfo, groups.get("Kids Tickets"))
        goue = _sum_by_names(tinfo, groups.get("Goue Kraal"))
        total_included = ga + kids + goue

        yday_delta = yesterday_delta(show["event_guid"], tz)
        days_to = _days_to_event_from_eventdate(js.get("EventDate"), tz)

        blocks.append({
            "name": show["name"],
            "capacity": int(show.get("capacity", 0)),
            "ga": ga,
            "kids": kids,
            "goue": goue,
            "total": total_included,
            "yesterday": yday_delta,
            "days_to_event": days_to,
        })

    # -------- Quicket blocks --------
    quicket_blocks = []
    if QUICKET_EVENTS:
        for ev in QUICKET_EVENTS:
            ev_id = int(ev["id"])
            name = ev["name"]
            capacity = int(ev.get("capacity", 0))
            groups = ev.get("groups", {})

            # live counts
            sums = quicket_summarize(ev_id, groups)  # adults, kids, total, ...
            adults = int(sums["adults"])
            kids = int(sums["kids"])
            total_included = int(sums["total"])

            # yesterday from nightly snapshots (namespaced key)
            yday = yesterday_delta(f"quicket:{ev_id}", tz)

            # event date: prefer manual override date-only, else cheap first-page probe
            qdate = None
            override_date = ev.get("event_date_date")  # "YYYY-MM-DD"
            if override_date:
                try:
                    qdate = datetime.strptime(override_date, "%Y-%m-%d").date()
                except Exception:
                    qdate = None
            if qdate is None:
                qdate = get_event_date_first_page(ev_id, tz)  # returns date or None

            days_to = _days_to(qdate, tz)

            quicket_blocks.append({
                "name": name,
                "capacity": capacity,
                "ga": adults,
                "kids": kids,
                "goue": 0,                 # keep field for unified formatter
                "total": total_included,
                "yesterday": yday,
                "days_to_event": days_to,
            })

    # -------- Shopify --------
    shop = None
    if CFG.get("SHOPIFY_BASE") and CFG.get("SHOPIFY_ACCESS_TOKEN"):
        try:
            shop = get_shopify_last7_summary()
        except Exception as e:
            # Non-fatal: still build the rest
            print(f"[WARN] Shopify fetch failed: {e}")

    # -------- Build final message --------
    msg = build_message(blocks, tz=tz, shopify=shop, quicket=quicket_blocks or None)
    return msg


def run():
    """Normal run: generate + email."""
    msg = generate_summary_text()
    # You can keep a fixed subject to keep a single thread; or include date.
    # subject = "Spoegwolf Daaglikse Opsomming"
    # If you prefer date in subject:
    now = datetime.now(pytz.timezone(CFG["TZ"]))
    subject = f"Spoegwolf Daaglikse Opsomming — {now.strftime('%A, %d %B %Y')}"
    send_email_summary(subject, msg)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Spoegwolf Daily Summary")
    parser.add_argument("--no-email", action="store_true",
                        help="Generate and print the summary without sending email (testing mode)")
    args = parser.parse_args()

    if args.no_email:
        print(generate_summary_text())
    else:
        run()