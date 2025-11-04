from .config import CFG, SHOWS
from .data_sources.plankton import get_event_summary
from .summarize_af import build_message

def _norm(s: str) -> str:
    # Tolerate extra spaces/case differences (e.g., "Honorary Ranger ")
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

def run():
    blocks = []
    for show in SHOWS:
        js = get_event_summary(show["event_guid"])
        tinfo = js.get("TicketInfo", [])  # per your sample

        groups = show.get("groups", {})
        ga = _sum_by_names(tinfo, groups.get("GA (Adults)"))
        kids = _sum_by_names(tinfo, groups.get("Kids Tickets"))
        goue = _sum_by_names(tinfo, groups.get("Goue Kraal"))
        excluded = _sum_excluded(tinfo, groups.get("exclude"))

        # “Total” = included groups only (GA + Kids + Goue), excludes e.g. Physical, Honorary
        total = ga + kids + goue

        blocks.append({
            "name": show["name"],
            "capacity": show["capacity"],
            "ga": ga,
            "kids": kids,
            "goue": goue,
            "total": total,
            # Optional debugging fields:
            # "excluded": excluded,
            # "raw_total_ticketsIssued": int(js.get("TotalTicketsIssued") or 0),
        })

    msg = build_message(blocks, tz=CFG["TZ"])
    print(msg)

if __name__ == "__main__":
    run()