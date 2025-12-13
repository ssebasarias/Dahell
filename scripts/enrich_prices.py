#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_prices.py
Recoge observaciones de precio desde varias fuentes y las inserta en `market_prices`.
Luego puedes consolidar en `product_price_stats` (vista) y copiar a products_raw.

Fuentes soportadas:
- MercadoLibre MCO (pública)
- SerpAPI (Google Shopping) — opcional

Requisitos:
  pip install duckdb requests python-dotenv
"""

import os, re, time, requests, duckdb
from urllib.parse import quote_plus
from dotenv import load_dotenv
from difflib import SequenceMatcher

load_dotenv()

DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "300"))

UA = {"User-Agent": "Mozilla/5.0 (+enrich_prices.py)"}
session = requests.Session()
session.headers.update(UA)

def norm_query(name: str, sku: str|None) -> str:
    if not name:
        name = ""
    q = re.sub(r"[\|\[\]\(\)–—•☆★✅✳️✓✔️❌]", " ", name)
    q = re.sub(r"\s+", " ", q).strip()
    if sku and sku.lower() not in q.lower():
        q = f"{q} {sku}"
    return q

def title_confidence(a: str, b: str) -> float:
    a = (a or "").lower()
    b = (b or "").lower()
    return SequenceMatcher(None, a, b).ratio()

def meli_prices(query: str, limit: int = 10):
    url = f"https://api.mercadolibre.com/sites/MCO/search?q={quote_plus(query)}&limit={limit}"
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        obs = []
        for it in data.get("results", []):
            price = it.get("price")
            curr  = it.get("currency_id") or "COP"
            title = it.get("title") or ""
            link  = it.get("permalink") or ""
            if price:
                obs.append({"source": "meli", "title": title, "price": float(price), "currency": curr, "product_url": link})
        return obs
    except Exception:
        return []

def serpapi_prices(query: str, gl="co", hl="es", num=10):
    if not SERPAPI_KEY:
        return []
    url = "https://serpapi.com/search.json"
    params = {"engine": "google_shopping", "q": query, "gl": gl, "hl": hl, "api_key": SERPAPI_KEY, "num": num}
    try:
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        out = []
        for item in data.get("shopping_results", []):
            title = item.get("title") or ""
            link  = item.get("link") or ""
            price_str = item.get("price")
            price_val = None
            if price_str:
                digits = re.sub(r"[^\d\.]", "", price_str.replace(",", ""))
                try:
                    price_val = float(digits)
                except Exception:
                    price_val = None
            if price_val:
                out.append({"source": "serpapi_google", "title": title, "price": price_val, "currency": "COP", "product_url": link})
        return out
    except Exception:
        return []

def main():
    con = duckdb.connect(DB_PATH)

    rows = con.execute("""
        SELECT id, sku, name
        FROM products_raw
        ORDER BY capture_ts DESC NULLS LAST
        LIMIT ?
    """, [BATCH_SIZE]).fetchall()

    if not rows:
        print("✅ No hay productos para enriquecer precios.")
        return

    inserted = 0
    for pid, sku, name in rows:
        q = norm_query(name or "", sku)
        obs = []
        obs += meli_prices(q, limit=8); time.sleep(0.2)
        obs += serpapi_prices(q, num=8)

        for o in obs:
            conf = title_confidence(name or "", o["title"])
            o["confidence"] = conf

        for o in obs:
            con.execute("""
                INSERT OR REPLACE INTO market_prices
                (product_id, source, title_normalized, price, currency, product_url, image_url_source, captured_at, confidence)
                VALUES (?, ?, ?, ?, ?, ?, NULL, CURRENT_TIMESTAMP, ?)
            """, [pid, o["source"], o["title"], o["price"], o["currency"], o["product_url"], o["confidence"]])
            inserted += 1

    print(f"💰 Observaciones de precio insertadas/actualizadas: {inserted}")
    con.close()

if __name__ == "__main__":
    main()
