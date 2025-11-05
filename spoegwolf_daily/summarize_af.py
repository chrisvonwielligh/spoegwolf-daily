from datetime import datetime
import pytz

_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrydag","Saterdag","Sondag"]
_MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie",
           "Augustus","September","Oktober","November","Desember"]

def _af_date(dt: datetime) -> str:
    dname = _DAYS[dt.weekday()]
    return f"{dname}, {dt.day:02d} {_MONTHS[dt.month-1]} {dt.year}"

def build_message(shows_blocks, tz="Africa/Johannesburg", shopify=None, quicket=None) -> str:
    za = pytz.timezone(tz)
    today = datetime.now(za)
    stamp = _af_date(today)

    lines = []
    lines.append(f"Spoegwolf Daaglikse Opsomming — {stamp}\n")
    lines.append("🎟️ *Kaartjies vir eie shows*\n")

    # PLANKTON
    lines.append("PLANKTON\n")
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
        lines.append(f"Sold Out % (Uit {cap:,}): {pct}%\n")

    # --- NEW: Quicket section (if present) ---
    if quicket:
        lines.append("QUICKET\n")
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
            lines.append(f"Sold Out % (Uit {cap:,}): {pct}%\n")

    # Shopify (unchanged)
    if shopify:
        lines.append("🛒 *Shopify Online Store*\n")
        lines.append(f"Sales in last 7 days: R{shopify['gross_sales']:.2f}")
        if shopify.get("top_item"):
            ti = shopify["top_item"]
            lines.append(f"Top selling item: {ti['title']} (x{ti['qty']})\n")

    return "\n".join(lines).rstrip()  # tidy end