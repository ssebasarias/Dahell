#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza `products_raw.phash` para filas con phash NULL y image_url válido.
Usa el mismo cálculo de pHash firmado que loader.py para mantener consistencia.
Requisitos:
  pip install duckdb pillow imagehash requests python-dotenv
Variables:
  DUCKDB_PATH  (ruta a tu .duckdb)
  BATCH_SIZE   (opcional, default 200)
  TIMEOUT      (opcional, default 10)
"""
import os, io, requests, duckdb, imagehash
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

DB_PATH   = os.getenv("DUCKDB_PATH", "db/dropi.db")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
TIMEOUT    = int(os.getenv("TIMEOUT", "10"))

def compute_phash_signed(img):
    h = int(str(imagehash.phash(img)), 16)
    return h - (1 << 64) if h >= (1 << 63) else h

def download_image(url, timeout=TIMEOUT):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")

def main():
    con = duckdb.connect(DB_PATH)
    total_missing = con.execute(
        "SELECT COUNT(*) FROM products_raw WHERE phash IS NULL AND image_url IS NOT NULL AND image_url <> ''"
    ).fetchone()[0]
    print(f"🔎 Registros sin pHash: {total_missing}")

    processed = 0
    while True:
        rows = con.execute("""
            SELECT id, image_url
            FROM products_raw
            WHERE phash IS NULL AND image_url IS NOT NULL AND image_url <> ''
            LIMIT ?
        """, [BATCH_SIZE]).fetchall()

        if not rows:
            break

        for pid, url in rows:
            try:
                img = download_image(url, timeout=TIMEOUT)
                ph = compute_phash_signed(img)
            except Exception as e:
                print(f"⚠️  id={pid} error descargando/calculando pHash: {e}")
                ph = None

            con.execute("UPDATE products_raw SET phash = ? WHERE id = ?", [ph, pid])
            processed += 1
            if processed % 50 == 0:
                print(f"✅ Actualizados {processed}…")

    print(f"🏁 Listo. Total actualizados: {processed}")
    con.close()

if __name__ == "__main__":
    main()
