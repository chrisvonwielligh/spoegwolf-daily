import smtplib, ssl, html, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import CFG

def _clean(s: str) -> str:
    return (s or "").replace("\u00A0","").strip()

def _text_to_html(body_text: str) -> str:
    """
    WhatsApp-like spacing with minimal HTML to avoid Gmail clipping:
    - Blank text lines -> extra <br> (visible gap between shows)
    - First non-empty line of each block -> <strong>Show Name</strong>
    - Bold numeric part of 'Total Sold: ...'
    - No CSS, tiny markup
    """
    esc = lambda t: html.escape(t, quote=False)
    lines = body_text.splitlines()
    out = []
    in_block = False

    for raw in lines:
        line = raw.rstrip("\r")
        stripped = line.strip()

        # Blank line => block break (double <br> total: one for previous line + one here)
        if stripped == "":
            out.append("<br>")
            in_block = False
            continue

        # First line of a block = show name (skip global headings)
        if (not in_block
            and ":" not in stripped
            and not stripped.startswith("🎟️")
            and not stripped.startswith("🛒")
            and not stripped.startswith("Spoegwolf")):
            out.append(f"<strong>{esc(stripped)}</strong><br>")
            in_block = True
            continue

        # Bold numeric part of "Total Sold: ..."
        low = stripped.lower()
        if low.startswith("total sold:"):
            label, _, value = stripped.partition(":")
            out.append(f"{esc(label)}:<strong>{esc(value)}</strong><br>")
            continue

        # Default
        out.append(f"{esc(line)}<br>")

    html_body = "\n".join(out)
    return f"""<!doctype html>
<html>
  <body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;">
{html_body}
  </body>
</html>"""

def send_email_summary(subject: str, body_text: str):
    host = CFG.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(CFG.get("EMAIL_PORT", "465"))
    user = _clean(CFG.get("EMAIL_USER"))
    password = _clean(CFG.get("EMAIL_PASS"))
    recipients = [r.strip() for r in (CFG.get("EMAIL_TO") or "").split(",") if r.strip()]

    missing = [k for k,v in [("EMAIL_USER",user),("EMAIL_PASS",password),("EMAIL_TO",",".join(recipients))] if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    # Build multipart/alternative (plain + HTML)
    msg = MIMEMultipart("alternative")
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    html_body = _text_to_html(body_text)

    # Plaintext part (what you already generate)
    part_text = MIMEText(body_text, "plain", "utf-8")
    # HTML part with bold styling
    part_html = MIMEText(html_body, "html", "utf-8")

    msg.attach(part_text)
    msg.attach(part_html)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=ctx) as server:
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
    print(f"✅ Email sent to {recipients}")