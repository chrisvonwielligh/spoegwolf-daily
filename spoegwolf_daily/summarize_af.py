from datetime import datetime
import pytz

_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrydag","Saterdag","Sondag"]
_MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie",
           "Augustus","September","Oktober","November","Desember"]

def _af_date(dt: datetime) -> str:
    dname = _DAYS[dt.weekday()]
    return f"{dname}, {dt.day:02d} {_MONTHS[dt.month-1]} {dt.year}"

# spoegwolf_daily/summarize_af.py

def build_message(shows_blocks, tz="Africa/Johannesburg", shopify=None, quicket=None, itickets=None) -> str:
    lines = []

    # ===== Shopify first =====
    if shopify:
        lines.append("🛒 *Shopify Online Store*")
        lines.append(f"Yesterdays Sales: R{shopify['yesterday_sales']:.2f}")
        lines.append(f"Sales this week: R{shopify['gross_sales']:.2f}")
        if shopify.get("top_item"):
            ti = shopify["top_item"]
            lines.append(f"Top Selling Item: {ti['title']} (x{ti['qty']})")
        lines.append("")  # blank line gap

    # ===== Plankton (your own shows) =====
    lines.append("🎟️ PLANKTON")
    lines.append("")
    for b in shows_blocks:
        name = b["name"]; cap = b["capacity"]
        ga = b["ga"]; kids = b["kids"]; goue = b["goue"]
        total = b["total"]; yday = b.get("yesterday"); days_to = b.get("days_to_event")
        pct = 0 if cap <= 0 else round(100 * total / cap)

        lines.append(f"{name}")
        lines.append(f"Gister se verkope: {'NVT' if yday is None else yday}")
        if days_to is not None:
            lines.append(f"dae tot die show: {days_to}")
        lines.append(f"GA (Adults): {ga}")
        lines.append(f"Kids Tickets: {kids}")
        if goue:
            lines.append(f"Goue Kraal: {goue}")
        lines.append(f"Total Sold: {total}")
        lines.append(f"Sold Out % (Uit {cap:,}): {pct}%")
        lines.append("")

    # ===== Quicket (if any) =====
    if quicket:
        lines.append("🎟️ QUICKET")
        lines.append("")
        for b in quicket:
            name = b["name"]; cap = b["capacity"]
            ga = b["ga"]; kids = b["kids"]; goue = b["goue"]
            total = b["total"]; yday = b.get("yesterday"); days_to = b.get("days_to_event")
            pct = 0 if cap <= 0 else round(100 * total / cap)

            lines.append(f"{name}")
            lines.append(f"Gister se verkope: {'NVT' if yday is None else yday}")
            if days_to is not None:
                lines.append(f"dae tot die show: {days_to}")
            lines.append(f"GA (Adults): {ga}")
            lines.append(f"Kids Tickets: {kids}")
            if goue:
                lines.append(f"Goue Kraal: {goue}")
            lines.append(f"Total Sold: {total}")
            lines.append(f"Sold Out % (Uit {cap:,}): {pct}%")
            lines.append("")

        # ===== iTickets =====
    if itickets:
        lines.append("🎟️ *iTickets shows*")
        lines.append("")
        for b in itickets:
            name = b["name"]
            cap = int(b.get("capacity", 0))
            yday = b.get("yesterday")
            days_to = b.get("days_to_event")

            normal = int(b.get("normal", 0))
            vip = int(b.get("vip", 0))
            total = int(b.get("total", normal + vip))

            lines.append(f"{name}")
            lines.append(f"Gister se verkope: {'NVT' if yday is None else yday}")
            if days_to is not None:
                lines.append(f"dae tot die show: {days_to}")
            groups = b.get("groups") or {}
            if groups:
                gcap = int(b.get("group_capacity", 0))
                for label, n in groups.items():
                    if gcap > 0:
                        lines.append(f"{label}: {n} ({round(100 * n / gcap)}% van {gcap:,})")
                    else:
                        lines.append(f"{label}: {n}")
                if b.get("other"):
                    lines.append(f"Ander: {b['other']}")
            else:
                lines.append(f"Normal: {normal}")
                if b.get("show_vip", True):
                    lines.append(f"VIP: {vip}")
            lines.append(f"Total Sold: {total}")

            if cap > 0:
                pct = round(100 * total / cap)
                lines.append(f"Sold Out % (Uit {cap:,}): {pct}%")

            lines.append("")

    return "\n".join(lines).rstrip()