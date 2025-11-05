from .config import CFG, SHOWS
from .data_sources.plankton import get_event_summary
from .snapshot_store import save_snapshot
from datetime import datetime
import pytz

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

def run():
    tz = pytz.timezone(CFG["TZ"])
    today_str = datetime.now(tz).date().isoformat()
    any_changed = False

    for show in SHOWS:
        js = get_event_summary(show["event_guid"])
        tinfo = js.get("TicketInfo", [])
        groups = show.get("groups", {})
        ga   = _sum_by_names(tinfo, groups.get("GA (Adults)"))
        kids = _sum_by_names(tinfo, groups.get("Kids Tickets"))
        goue = _sum_by_names(tinfo, groups.get("Goue Kraal"))
        total_included = ga + kids + goue

        changed = save_snapshot(show["event_guid"], today_str, total_included)
        any_changed = any_changed or changed
        print(f"[snapshot] {show['name']} {today_str} = {total_included} ({'saved' if changed else 'unchanged'})")

    return 0

if __name__ == "__main__":
    raise SystemExit(run())