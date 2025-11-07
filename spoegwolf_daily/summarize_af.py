from datetime import datetime
import pytz

_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrydag","Saterdag","Sondag"]
_MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie",
           "Augustus","September","Oktober","November","Desember"]

def _af_date(dt: datetime) -> str:
    dname = _DAYS[dt.weekday()]
    return f"{dname}, {dt.day:02d} {_MONTHS[dt.month-1]} {dt.year}"

# spoegwolf_daily/summarize_af.py

def build_message(shows_blocks, tz="Africa/Johannesburg", shopify=None, quicket=None) -> str:
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
    lines.append("🎟️ *Kaartjies vir eie shows*")
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
        lines.append("🎟️ *Quicket shows*")
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

    return "\n".join(lines).rstrip()