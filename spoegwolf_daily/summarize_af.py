from datetime import datetime
import pytz

_DAYS = ["Maandag","Dinsdag","Woensdag","Donderdag","Vrydag","Saterdag","Sondag"]
_MONTHS = ["Januarie","Februarie","Maart","April","Mei","Junie","Julie",
           "Augustus","September","Oktober","November","Desember"]

def _af_date(dt: datetime) -> str:
    dname = _DAYS[dt.weekday()]
    return f"{dname}, {dt.day:02d} {_MONTHS[dt.month-1]} {dt.year}"

def build_message(shows_blocks, tz="Africa/Johannesburg") -> str:
    za = pytz.timezone(tz)
    today = datetime.now(za)
    stamp = _af_date(today)

    lines = []
    lines.append(f"Spoegwolf Daaglikse Opsomming — {stamp}\n")
    lines.append("🎟️ *Kaartjies vir eie shows*\n")

    for b in shows_blocks:
        name = b["name"]
        cap = b["capacity"]
        ga = b["ga"]
        kids = b["kids"]
        goue = b["goue"]
        total = b["total"]

        pct = 0 if cap <= 0 else round(100 * total / cap)

        lines.append(f"{name}")
        lines.append(f"GA (Adults): {ga}")
        lines.append(f"Kids Tickets: {kids}")
        lines.append(f"Goue Kraal: {goue}")
        lines.append(f"Total Sold: {total}")
        lines.append(f"Sold Out % (Uit {cap:,}): {pct}%\n")

    return "\n".join(lines).strip()