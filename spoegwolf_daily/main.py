# spoegwolf_daily/main.py

from datetime import datetime
import pytz

from .config import CFG, SHOWS, QUICKET_EVENTS
from .data_sources.quicket import summarize_event as quicket_summarize, get_event_date_first_page
from .data_sources.plankton import get_event_summary
from .data_sources.shopify import get_shopify_last7_summary
from .summarize_af import build_message
from .senders.emailer import send_email_summary
from .snapshot_store import yesterday_delta


# ---- helpers (restored) ----
def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _sum_by_names(ticket_info, wanted_names):
    wanted = {_norm(n) for n in (wanted_names or [])}
    total = 0
    for t in (ticket_info or []):
        name = _norm(t.get("ticketName"))
        if name in wanted:
            total += int(t.get("ticketsIssued") or 0)
    return total

def _sum_excluded(ticket_info, exclude_names):
    excl = {_norm(n) for n in (exclude_names or [])}
    total = 0
    for t in (ticket_info or []):
        name = _norm(t.get("ticketName"))
        if name in excl:
            total += int(t.get("ticketsIssued") or 0)
    return total

def _event_date_za_date(event_iso: str, tz_name: str):
    """
    Parse Plankton EventDate (e.g., '2026-01-31T10:15:00' or with 'Z'/offset)
    and return the event's DATE in Africa/Johannesburg.
    """
    if not event_iso:
        return None
    za = pytz.timezone(tz_name)
    txt = event_iso.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(txt)  # handles explicit offsets
    except ValueError:
        try:
            dt = datetime.strptime(event_iso[:19], "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None
    # If no tzinfo, assume local ZA; else convert to ZA then take .date()
    if dt.tzinfo is None:
        dt = za.localize(dt)
    else:
        dt = dt.astimezone(za)
    return dt.date()

def _days_to_event_from_eventdate(event_iso: str, tz_name: str):
    ev_date = _event_date_za_date(event_iso, tz_name)
    if ev_date is None:
        return None
    today = datetime.now(pytz.timezone(tz_name)).date()
    return (ev_date - today).days


def generate_summary_text() -> str:
    """
    Build and return the full summary message without sending email.
    Safe for testing: read-only (no writes).
    """
    blocks = []
    for show in SHOWS:
        try:
            js = get_event_summary(show["event_guid"])
            tinfo = js.get("TicketInfo", [])

            groups = show.get("groups", {})
            ga   = _sum_by_names(tinfo, groups.get("GA (Adults)"))
            kids = _sum_by_names(tinfo, groups.get("Kids Tickets"))
            goue = _sum_by_names(tinfo, groups.get("Goue Kraal"))
            total_included = ga + kids + goue

            days_to = _days_to_event_from_eventdate(js.get("EventDate"), CFG["TZ"])

            from .snapshot_store import yesterday_delta
            yday_delta = yesterday_delta(show["event_guid"], CFG["TZ"])

            blocks.append({
                "name": show["name"],
                "capacity": show["capacity"],
                "ga": ga,
                "kids": kids,
                "goue": goue,
                "total": total_included,
                "yesterday": yday_delta,
                "days_to_event": days_to,
            })
        except Exception as e:
            # Show a stub block with the error, but keep the rest of the summary
            blocks.append({
                "name": f"{show['name']} (kon nie laai nie)",
                "capacity": show["capacity"],
                "ga": 0, "kids": 0, "goue": 0, "total": 0,
                "yesterday": None,
                "days_to_event": None,
            })
            # Print to console so you see why during tests
            print(f"[WARN] Plankton fetch failed for {show['name']}: {e}")

    # ---- Quicket blocks ----
    quicket_blocks = []
    for ev in QUICKET_EVENTS:
        ev_id = ev["id"]
        name = ev["name"]
        capacity = int(ev.get("capacity", 0))
        groups = ev.get("groups", {})

        sums = quicket_summarize(ev_id, groups)
        adults = int(sums["adults"])
        kids = int(sums["kids"])
        total_included = int(sums["total"])

        # Yesterday delta from snapshots (read-only), namespaced key
        yday = yesterday_delta(f"quicket:{ev_id}", CFG["TZ"])

        # Event date: prefer manual override (YYYY-MM-DD), else probe first page
        qdate = None
        override_date = ev.get("event_date_date")  # "YYYY-MM-DD"
        if override_date:
            try:
                qdate = datetime.strptime(override_date, "%Y-%m-%d").date()
            except Exception:
                qdate = None
        if qdate is None:
            qdate = get_event_date_first_page(ev_id, CFG["TZ"])

        days_to = _days_to(qdate, CFG["TZ"])

        quicket_blocks.append({
            "name": name,
            "capacity": capacity,
            "ga": adults,
            "kids": kids,
            "goue": 0,
            "total": total_included,
            "yesterday": yday,
            "days_to_event": days_to,
        })

    # Shopify block (kept exactly as in run)
    shop = None
    if CFG.get("SHOPIFY_BASE") and CFG.get("SHOPIFY_ACCESS_TOKEN"):
        from .data_sources.shopify import get_shopify_last7_summary
        shop = get_shopify_last7_summary()

    msg = build_message(blocks, tz=CFG["TZ"], shopify=shop, quicket=quicket_blocks)
    return msg


def _days_to(d, tz_name: str):
    if not d:
        return None
    today = datetime.now(pytz.timezone(tz_name)).date()
    return (d - today).days
# ---- end helpers ----


def run():
    blocks = []
    for show in SHOWS:
        js = get_event_summary(show["event_guid"])
        tinfo = js.get("TicketInfo", [])

        groups = show.get("groups", {})
        ga   = _sum_by_names(tinfo, groups.get("GA (Adults)"))
        kids = _sum_by_names(tinfo, groups.get("Kids Tickets"))
        goue = _sum_by_names(tinfo, groups.get("Goue Kraal"))
        _   = _sum_excluded(tinfo, groups.get("exclude"))  # excluded, not counted

        total_included = ga + kids + goue

        # store today’s snapshot and compute "yesterday" delta
        yday_delta = yesterday_delta(show["event_guid"], CFG["TZ"])

        # days to event from EventDate
        days_to = _days_to_event_from_eventdate(js.get("EventDate"), CFG["TZ"])

        blocks.append({
            "name": show["name"],
            "capacity": show["capacity"],
            "ga": ga,
            "kids": kids,
            "goue": goue,
            "total": total_included,
            "yesterday": yday_delta,
            "days_to_event": days_to,
        })

    # Shopify (only if configured)
    shop = None
    if CFG.get("SHOPIFY_BASE") and CFG.get("SHOPIFY_ACCESS_TOKEN"):
        shop = get_shopify_last7_summary()

    msg = build_message(blocks, tz=CFG["TZ"], shopify=shop)
    print(msg)

    subject = "Spoegwolf Daaglikse Opsomming"
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