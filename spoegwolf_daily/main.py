# spoegwolf_daily/main.py

from datetime import datetime
import pytz

from .config import CFG, SHOWS
from .data_sources.plankton import get_event_summary
from .data_sources.shopify import get_shopify_last7_summary
from .summarize_af import build_message
from .state import update_and_get_yesterday_delta


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
        yday_delta = update_and_get_yesterday_delta(
            show["event_guid"], total_included, CFG["TZ"]
        )

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


if __name__ == "__main__":
    run()