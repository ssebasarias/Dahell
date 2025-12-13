#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_images.py
Rellena imágenes faltantes consultando varias fuentes y guarda candidatos en `product_assets`.
También puede fijar una imagen canónica en products_raw (si no existe) según reglas simples.

Fuentes soportadas (configurables por .env):
- Google CSE (JSON API): GOOGLE_CSE_ID, GOOGLE_API_KEY
- Bing Image Search (Azure): BING_API_KEY
- MercadoLibre (pública): site MCO (Colombia)

Requisitos:
  pip install duckdb pillow imagehash requests python-dotenv

Variables .env:
  DUCKDB_PATH=db/dropi.db
  GOOGLE_CSE_ID=
  GOOGLE_API_KEY=
  BING_API_KEY=
  SOURCE_DOMAINS="falabella.com.co,exito.com,alkosto.com,ktronix.com,mercadolibre.com.co,linio.com.co"
  BATCH_SIZE=200
  MIN_WIDTH=400
  MIN_HEIGHT=400
  OVERWRITE_CANONICAL=0   # 1 para permitir reemplazar image_url/phash ya existentes si la nueva es mejor
"""

import os, re, io, json, time, hashlib, requests, duckdb, imagehash
from PIL import Image
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BING_API_KEY = os.getenv("BING_API_KEY")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "150"))
MIN_W = int(os.getenv("MIN_WIDTH", "400"))
MIN_H = int(os.getenv("MIN_HEIGHT", "400"))
OVERWRITE = os.getenv("OVERWRITE_CANONICAL", "0") in ("1","true","yes","True")

RAW_DOMAINS = os.getenv("SOURCE_DOMAINS", "").strip()
SOURCE_DOMAINS = [d.strip() for d in RAW_DOMAINS.split(",") if d.strip()]

UA = {"User-Agent": "Mozilla/5.0 (+enrich_images.py)"}
session = requests.Session()
session.headers.update(UA)

def compute_phash_signed(pil_img):
    h = int(str(imagehash.phash(pil_img)), 16)
    return h - (1 << 64) if h >= (1 << 63) else h

def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()

def norm_query(name: str, sku: str|None) -> str:
    if not name:
        name = ""
    q = re.sub(r"[\|\[\]\(\)–—•☆★✅✳️✓✔️❌]", " ", name)
    q = re.sub(r"\s+", " ", q).strip()
    if sku and sku.lower() not in q.lower():
        q = f"{q} {sku}"
    return q

def meli_search(query: str, limit: int = 6):
    url = f"https://api.mercadolibre.com/sites/MCO/search?q={quote_plus(query)}&limit={limit}"
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        out = []
        for it in data.get("results", []):
            thumb = it.get("thumbnail") or ""
            link  = it.get("permalink") or ""
            title = it.get("title") or ""
            if thumb:
                out.append({"image": thumb, "link": link, "title": title, "source": "meli"})
        return out
    except Exception:
        return []

def google_cse_images(query: str, num: int = 6):
    if not (GOOGLE_CSE_ID and GOOGLE_API_KEY):
        return []
    if SOURCE_DOMAINS:
        sites = " OR ".join([f"site:{d}" for d in SOURCE_DOMAINS])
        q = f"{query} ({sites})"
    else:
        q = query
    url = ("https://www.googleapis.com/customsearch/v1?"
           f"key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={quote_plus(q)}&searchType=image&num={num}")
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        out = []
        for item in data.get("items", []):
            link = item.get("link")
            title = item.get("title") or ""
            if link:
                out.append({"image": link, "link": link, "title": title, "source": "google_cse"})
        return out
    except Exception:
        return []

def bing_image_search(query: str, count: int = 6):
    if not BING_API_KEY:
        return []
    url = "https://api.bing.microsoft.com/v7.0/images/search"
    params = {"q": query, "count": count, "mkt": "es-CO", "safeSearch": "Off"}
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY, **UA}
    try:
        r = session.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        out = []
        for v in data.get("value", []):
            link = v.get("contentUrl")
            hostp = v.get("hostPageUrl") or link
            title = v.get("name") or ""
            if link:
                out.append({"image": link, "link": hostp, "title": title, "source": "bing"})
        return out
    except Exception:
        return []

def fetch_image(url: str):
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        ctype = r.headers.get("Content-Type", "")
        b = r.content
        img = Image.open(io.BytesIO(b)).convert("RGB")
        meta = {"mime": ctype, "sha1": sha1_bytes(b), "bytes": len(b)}
        return img, meta
    except Exception:
        return None, {}

def choose_canonical(assets):
    def src_rank(u: str) -> int:
        if not SOURCE_DOMAINS:
            return 0
        for i, d in enumerate(SOURCE_DOMAINS):
            if d in (u or ""):
                return -100 - i
        return 0
    if not assets:
        return None
    ranked = sorted(
        assets,
        key=lambda a: (src_rank(a.get("image_url","")), -(a.get("width",0)*a.get("height",0)))
    )
    return ranked[0] if ranked else None

def main():
    con = duckdb.connect(DB_PATH)

    rows = con.execute("""
        SELECT id, sku, name, COALESCE(image_url, '') AS image_url
        FROM products_raw
        WHERE (image_url IS NULL OR image_url = '')
           OR phash IS NULL
        LIMIT ?
    """, [BATCH_SIZE]).fetchall()

    if not rows:
        print("✅ No hay productos pendientes de imagen.")
        return

    print(f"🔎 Procesando {len(rows)} productos pendientes…")

    inserted_assets = 0
    updated_canonical = 0

    for pid, sku, name, image_url in rows:
        query = norm_query(name or "", sku)
        candidates = []

        candidates += google_cse_images(query, num=6); time.sleep(0.2)
        candidates += bing_image_search(query, count=6); time.sleep(0.2)
        candidates += meli_search(query, limit=6)

        seen_urls = set()
        found_assets = []

        for c in candidates:
            img_url = c.get("image")
            if not img_url or img_url in seen_urls:
                continue
            seen_urls.add(img_url)

            img, meta = fetch_image(img_url)
            if img is None:
                con.execute("""
                    INSERT OR REPLACE INTO product_assets
                    (product_id, image_url, source, status, download_ts)
                    VALUES (?, ?, ?, '404', CURRENT_TIMESTAMP)
                """, [pid, img_url, c.get("source","unknown")])
                continue

            w, h = img.width, img.height
            if w < MIN_W or h < MIN_H:
                con.execute("""
                    INSERT OR REPLACE INTO product_assets
                    (product_id, image_url, source, status, width, height, mime, bytes_sha1, download_ts)
                    VALUES (?, ?, ?, 'too_small', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, [pid, img_url, c.get("source","unknown"), w, h, meta.get("mime",""), meta.get("sha1","")])
                continue

            ph = compute_phash_signed(img)
            con.execute("""
                INSERT OR REPLACE INTO product_assets
                (product_id, image_url, source, status, phash, width, height, mime, bytes_sha1, download_ts)
                VALUES (?, ?, ?, 'ok', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, [pid, img_url, c.get("source","unknown"), ph, w, h, meta.get("mime",""), meta.get("sha1","")])
            inserted_assets += 1
            found_assets.append({
                "image_url": img_url, "width": w, "height": h, "phash": ph, "source": c.get("source","unknown")
            })

        if (not image_url or image_url == "") and found_assets:
            best = choose_canonical(found_assets)
            if best:
                con.execute("""
                    UPDATE products_raw
                    SET image_url = ?, phash = ?, image_source = ?, last_enriched_ts = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, [best["image_url"], best["phash"], best["source"], pid])
                updated_canonical += 1
        elif OVERWRITE and found_assets:
            current = None
            if image_url:
                try:
                    img, _ = fetch_image(image_url)
                    if img:
                        current = {"width": img.width, "height": img.height}
                except Exception:
                    current = None
            best = choose_canonical(found_assets)
            if best and (not current or (best["width"] * best["height"] > 2 * (current["width"]*current["height"]))):
                con.execute("""
                    UPDATE products_raw
                    SET image_url = ?, phash = ?, image_source = ?, last_enriched_ts = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, [best["image_url"], best["phash"], best["source"], pid])
                updated_canonical += 1

    print(f"🖼️  Assets insertados/actualizados: {inserted_assets}")
    print(f"📌 Canónicas actualizadas en products_raw: {updated_canonical}")
    con.close()

if __name__ == "__main__":
    main()
