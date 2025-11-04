# spoegwolf_daily/data_sources/shopify.py
"""
Shopify REST Admin fetcher:
- "Sales in last 7 days" (gross excluding shipping)
- "Top selling item" by quantity (last 7 days)

Assumptions:
- Store currency is ZAR (or you accept store currency as-is).
- Uses REST Admin API with a private/custom app access token.
- Pagination via Link headers.
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import time
import requests

from ..config import CFG


def _headers() -> Dict[str, str]:
    tok = CFG.get("SHOPIFY_ACCESS_TOKEN")
    if not tok:
        raise RuntimeError("Missing SHOPIFY_ACCESS_TOKEN in .env")
    return {
        "X-Shopify-Access-Token": tok,
        "Accept": "application/json",
        "User-Agent": "spoegwolf-daily/1.0",
    }


def _orders_url(start_iso_utc: str) -> str:
    base = (CFG.get("SHOPIFY_BASE") or "").rstrip("/")
    if not base:
        raise RuntimeError("Missing SHOPIFY_BASE in .env")
    # We keep it simple: created_at_min filters last 7 days in UTC
    return f"{base}/orders.json?status=any&limit=250&created_at_min={start_iso_utc}"


def _parse_link_next(link_header: Optional[str]) -> Optional[str]:
    """
    Extract the 'next' URL from Shopify's Link header.
    Example:
      <https://.../orders.json?page_info=XYZ&limit=250>; rel="next"
    """
    if not link_header:
        return None
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if 'rel="next"' in p:
            start = p.find("<") + 1
            end = p.find(">")
            if 0 < start < end:
                return p[start:end]
    return None


def _to_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _shipping_amount(order: Dict[str, Any]) -> float:
    """
    Prefer total_shipping_price_set.shop_money.amount; fallback to sum of shipping_lines[].price.
    """
    ship_total = 0.0

    # Preferred modern field
    try:
        ship_total = _to_float(order.get("total_shipping_price_set", {})
                                    .get("shop_money", {})
                                    .get("amount"))
    except Exception:
        ship_total = 0.0

    # Fallback for older responses if preferred field absent or zero
    if not ship_total:
        try:
            lines = order.get("shipping_lines") or []
            ship_total = sum(_to_float(s.get("price")) for s in lines)
        except Exception:
            ship_total = 0.0

    return max(0.0, ship_total)


def _net_order_total_excl_shipping(order: Dict[str, Any]) -> float:
    """
    Gross (total_price) minus shipping.
    Note: This does NOT subtract refunds; if you want net of refunds,
    we can extend this to query refunds per order.
    """
    total_price = _to_float(order.get("total_price"))
    ship_price = _shipping_amount(order)
    net = total_price - ship_price
    return max(0.0, net)


def get_shopify_last7_summary() -> Dict[str, Any]:
    """
    Returns:
      {
        "orders": int,
        "gross_sales": float,     # shipping excluded
        "top_item": {"title": str, "qty": int} or None
      }
    """
    # Start timestamp (UTC) for last 7 days
    start_utc = (datetime.now(timezone.utc) - timedelta(days=7)).replace(microsecond=0)
    start_iso = start_utc.isoformat().replace("+00:00", "Z")

    url = _orders_url(start_iso)
    headers = _headers()

    total_orders = 0
    gross_excl_shipping = 0.0
    item_counts: Dict[str, int] = {}

    # Basic loop with simple retry on 429 (rate limit)
    while url:
        for attempt in range(3):
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 429:  # rate limited
                # Back off briefly and retry
                time.sleep(2 + attempt)
                continue
            resp.raise_for_status()
            break  # OK

        data = resp.json() if resp.content else {}
        orders = data.get("orders", [])
        total_orders += len(orders)

        for o in orders:
            # Accumulate product-only gross (exclude shipping)
            gross_excl_shipping += _net_order_total_excl_shipping(o)

            # Count items by title (quantity)
            for li in (o.get("line_items") or []):
                title = (li.get("title") or "Unknown item").strip() or "Unknown item"
                qty = int(li.get("quantity") or 0)
                if qty > 0:
                    item_counts[title] = item_counts.get(title, 0) + qty

        url = _parse_link_next(resp.headers.get("Link"))

    # Determine top-selling item
    if item_counts:
        top_title, top_qty = max(item_counts.items(), key=lambda kv: kv[1])
        top_item = {"title": top_title, "qty": int(top_qty)}
    else:
        top_item = None

    return {
        "orders": int(total_orders),
        "gross_sales": round(gross_excl_shipping, 2),
        "top_item": top_item,
    }