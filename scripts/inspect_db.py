#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspección rápida de tu DuckDB para `products_raw`.
Requisitos: pip install duckdb python-dotenv
Usa DUCKDB_PATH del entorno o db/dropi.db por defecto.
"""
import os, duckdb
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")

con = duckdb.connect(DB_PATH)

print("== Conteo total ==")
print(con.execute("SELECT COUNT(*) AS total_rows FROM products_raw").fetchdf())

print("\n== Faltantes de pHash ==")
print(con.execute("SELECT COUNT(*) AS missing_phash FROM products_raw WHERE phash IS NULL").fetchdf())

print("\n== Faltantes de image_url ==")
print(con.execute("SELECT COUNT(*) AS missing_image_url FROM products_raw WHERE image_url IS NULL OR image_url = ''").fetchdf())

print("\n== Muestra reciente ==")
print(con.execute("""
SELECT id, sku, name, image_url, phash, capture_ts
FROM products_raw
ORDER BY capture_ts DESC NULLS LAST
LIMIT 20
""").fetchdf())

print("\n== Distribución por proveedor ==")
print(con.execute("""
SELECT COALESCE(user_id, -1) AS user_id, COALESCE(user_name, '(null)') AS user_name, COUNT(*) AS n
FROM products_raw
GROUP BY ALL
ORDER BY n DESC
""").fetchdf())

print("\n== Elegibles para calcular pHash ==")
print(con.execute("""
SELECT COUNT(*) AS eligibles
FROM products_raw
WHERE phash IS NULL AND image_url IS NOT NULL AND image_url <> ''
""").fetchdf())
