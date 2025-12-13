#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consolidate_prices.py
Lee la vista product_price_stats (p25/p50/p75) y actualiza products_raw con derivados:
- suggested_price_ext = p50 (mediana)
- price_p25/price_p50/price_p75
- last_enriched_ts, enrich_confidence

Requisitos:
  pip install duckdb python-dotenv
"""

import os, duckdb
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")

def main():
    con = duckdb.connect(DB_PATH)

    con.execute("""
        UPDATE products_raw pr
        SET suggested_price_ext = s.p50,
            price_p25 = s.p25,
            price_p50 = s.p50,
            price_p75 = s.p75,
            last_enriched_ts = CURRENT_TIMESTAMP,
            enrich_confidence = COALESCE(s.avg_confidence, enrich_confidence)
        FROM product_price_stats s
        WHERE pr.id = s.product_id
    """)

    df = con.execute("""
        SELECT COUNT(*) AS updated, AVG(enrich_confidence) AS avg_conf
        FROM products_raw
        WHERE last_enriched_ts IS NOT NULL
    """).fetchdf()
    print(df)

    con.close()

if __name__ == "__main__":
    main()
