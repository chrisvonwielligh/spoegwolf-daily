# spoegwolf_daily/data_sources/shopify.py
from __future__ import annotations

import os
import requests
import datetime as dt
from typing import Dict, Any, List, Optional
import pytz
from urllib.parse import urlparse

from ..config import CFG

# -------------------- config + helpers --------------------

def _normalize_base(raw: Optional[str]) -> str:
    """
    Accepts 'spoegwolf-2.myshopify.com' OR 'https://spoegwolf-2.myshopify.com[/anything]'
    and returns just 'spoegwolf-2.myshopify.com'.
    """
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        return (parsed.netloc or "").strip()
    # remove any accidental path fragments
    return raw.split("/")[0].strip()

BASE = _normalize_base(CFG.get("SHOPIFY_BASE"))
TOKEN = CFG.get("SHOPIFY_ACCESS_TOKEN")
# Use one API version. You can override via env secret SHOPIFY_API_VERSION.
API_VER = os.getenv("SHOPIFY_API_VERSION", "2024-10")

def _headers() -> Dict[str, str]:
    if not BASE or not TOKEN:
        raise RuntimeError("Missing SHOPIFY_BASE or SHOPIFY_ACCESS_TOKEN")
    return {
        "X-Shopify-Access-Token": TOKEN,
        "Accept": "application/json",
        "User-Agent": "spoegwolf-daily/1.0",
    }

def _orders_url() -> str:
    # Build a clean base URL: https://<host>/admin/api/<ver>/orders.json
    return f"https://{BASE}/admin/api/{API_VER}/orders.json"

def _iso_utc(dt_local: dt.datetime, tz_name: str) -> str:
    """
    Return an ISO UTC string for a datetime that may be naive (no tz) or aware.
    If naive: treat it as tz_name local time. If aware: convert from its tz.
    """
    tz = pytz.timezone(tz_name)
    if dt_local.tzinfo is None:
        loc = tz.localize(dt_local)
    else:
        loc = dt_local.astimezone(tz)
    return loc.astimezone(pytz.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

# -------------------- order parsing --------------------

def _sum_order_subtotal(order: Dict[str, Any]) -> float:
    """
    Return amount excluding shipping.
    Prefer 'current_subtotal_price' or 'subtotal_price' or 'total_line_items_price'.
    Fallback: sum line items price * quantity.
    """
    for k in ("current_subtotal_price", "subtotal_price", "total_line_items_price"):
        v = order.get(k)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass

    total = 0.0
    for li in (order.get("line_items") or []):
        try:
            total += float(li.get("price", 0.0)) * int(li.get("quantity", 0))
        except Exception:
            continue
    return total

def _pick_top_item(orders: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Return {'title': str, 'qty': int} for the most-sold line item in the provided orders.
    Uses quantity across all orders (7-day window).
    """
    counts: Dict[str, int] = {}
    for o in orders:
        for li in (o.get("line_items") or []):
            title = (li.get("title") or "").strip()
            qty = int(li.get("quantity") or 0)
            if not title or qty <= 0:
                continue
            counts[title] = counts.get(title, 0) + qty
    if not counts:
        return None
    title = max(counts, key=counts.get)
    return {"title": title, "qty": counts[title]}

# -------------------- API calls --------------------

def _fetch_orders(created_min_iso: str, created_max_iso: str, status: str = "paid") -> List[Dict[str, Any]]:
    """
    Fetch orders in [created_min, created_max] using REST with cursor pagination.
    We request 250 per page and follow Link headers (page_info).
    """
    orders: List[Dict[str, Any]] = []
    params = {
        "limit": 250,
        "status": "any",              # include all, then filter by financial_status
        "financial_status": status,   # paid only (you can change to 'any' if needed)
        "created_at_min": created_min_iso,
        "created_at_max": created_max_iso,
        "fields": ",".join([
            "id","created_at","currency",
            "current_subtotal_price","subtotal_price","total_line_items_price",
            "line_items","financial_status","cancelled_at"
        ]),
    }

    session = requests.Session()
    url = _orders_url()
    headers = _headers()

    while True:
        r = session.get(url, headers=headers, params=params, timeout=(5, 15))
        r.raise_for_status()
        data = r.json() or {}
        batch = data.get("orders") or []
        orders.extend(batch)

        # Pagination via Link header (absolute URL)
        link = r.headers.get("Link", "")
        if 'rel="next"' in link:
            try:
                part = [p for p in link.split(",") if 'rel="next"' in p][0]
                url = part.split(";")[0].strip().strip("<>")  # absolute URL with page_info
                params = None  # subsequent call uses the absolute URL (no extra params)
                continue
            except Exception:
                pass
        break

    # Filter: paid / partially paid, not cancelled
    clean: List[Dict[str, Any]] = []
    for o in orders:
        if o.get("cancelled_at"):
            continue
        if (o.get("financial_status") or "").lower() not in ("paid", "partially_paid"):
            continue
        clean.append(o)
    return clean

# -------------------- public API --------------------

def get_shopify_last7_summary() -> Dict[str, Any]:
    """
    Returns:
      {
        'yesterday_sales': float,  # ZAR, excl. shipping
        'gross_sales': float,      # last 7 days rolling, excl. shipping
        'top_item': {'title': str, 'qty': int} | None
      }
    """
    tz = CFG.get("TZ", "Africa/Johannesburg")
    za = pytz.timezone(tz)
    today = dt.datetime.now(za).date()

    # Yesterday (00:00–23:59 local)
    y0 = dt.datetime.combine(today - dt.timedelta(days=1), dt.time(0, 0, 0))
    y1 = dt.datetime.combine(today - dt.timedelta(days=1), dt.time(23, 59, 59))

    # Last 7 days window (rolling, up to now)
    w0 = dt.datetime.combine(today - dt.timedelta(days=6), dt.time(0, 0, 0))
    w1 = dt.datetime.now(za).replace(microsecond=0)

    y_orders = _fetch_orders(_iso_utc(y0, tz), _iso_utc(y1, tz))
    w_orders = _fetch_orders(_iso_utc(w0, tz), _iso_utc(w1, tz))

    y_total = sum(_sum_order_subtotal(o) for o in y_orders)
    w_total = sum(_sum_order_subtotal(o) for o in w_orders)

    top_item = _pick_top_item(w_orders)

    return {
        "yesterday_sales": float(round(y_total, 2)),
        "gross_sales": float(round(w_total, 2)),
        "top_item": top_item,
    }