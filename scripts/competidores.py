"""
Analiza los productos calmanentados en la base de datos DuckDB para encontrar productos similares o iguales pero con diferente proveedor o nombre.
"""

"""
peek_products.py – Lee una copia de la base DuckDB aunque la original esté bloqueada por escritura.

Uso:
    python peek_products.py --limit 10

Flujo:
1. Intenta abrir `DUCKDB_PATH` en modo READ_ONLY.
2. Si falla por lock de Windows (PermissionError / UnicodeDecodeError),
   hace una **copia en caliente** a un archivo temporal y abre esa copia.
3. Muestra las primeras filas con `tabulate`.

Requisitos:
    pip install duckdb python-dotenv pandas tabulate
"""
"""
compute_phash.py – Calcula pHash para productos que aún no lo tienen y actualiza products_raw.

Uso:
    python compute_phash.py --batch 500

Requisitos:
    pip install duckdb python-dotenv pillow imagehash requests tqdm

Notas:
* Mantiene la conexión abierta sólo el tiempo necesario para leer un lote y
  luego para hacer el UPDATE, de modo que minimiza bloqueos.
* Descarga la imagen mediante `requests` (stream) y calcula su pHash.
* Convierte el objeto `imagehash.ImageHash` (64‑bit) en `INT64` para almacenar.
"""
import argparse
import io
import os
import pathlib
import time
from typing import List, Tuple

import duckdb
import requests
from dotenv import load_dotenv
from PIL import Image
import imagehash
from tqdm import tqdm

# ── Config ──────────────────────────────────────────────────────────────
load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")
TIMEOUT = 5  # segundos para requests
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}

# ── Funciones ───────────────────────────────────────────────────────────

def fetch_batch(batch_size: int) -> List[Tuple[int, str]]:
    """Obtiene un lote (id, image_url) donde phash es NULL."""
    with duckdb.connect(DB_PATH) as con:
        rows = con.execute(
            """
            SELECT id, image_url
            FROM products_raw
            WHERE phash IS NULL AND image_url IS NOT NULL
            LIMIT ?
            """,
            [batch_size],
        ).fetchall()
    return rows


def compute_hash(url: str):
    try:
        resp = requests.get(url, stream=True, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        img_bytes = io.BytesIO(resp.content)
        with Image.open(img_bytes) as im:
            return int(imagehash.phash(im))  # convierte a int64
    except Exception:
        return None


def update_hashes(pairs: List[Tuple[int, int]]):
    with duckdb.connect(DB_PATH) as con:
        con.executemany(
            "UPDATE products_raw SET phash = ? WHERE id = ?",
            [(h, pid) for pid, h in pairs],
        )
        con.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=500, help="Tamaño del lote")
    args = parser.parse_args()

    rows = fetch_batch(args.batch)
    if not rows:
        print("✅ No quedan productos sin pHash.")
        return

    updated = []
    for pid, url in tqdm(rows, desc="Hashing"):
        h = compute_hash(url)
        if h is not None:
            updated.append((pid, h))

    if updated:
        update_hashes(updated)
        print(f"✔️  Actualizados {len(updated)} / {len(rows)} registros.")
    else:
        print("⚠️  No se pudo generar ningún hash en este lote.")


if __name__ == "__main__":
    main()
