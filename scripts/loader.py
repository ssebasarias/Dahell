"""
Modulo de carga de productos desde archivos JSONL a DuckDB.
Este script:
- Procesa todos los JSONL disponibles y sale al terminar.
- Descarga imágenes y calcula su hash perceptual (phash).
- Inserta registros en la tabla `products_raw` de DuckDB.
- Evita duplicados por ID.

Requisitos:
- Requiere las variables de entorno RAW_DIR y DUCKDB_PATH.
- Requiere que la tabla `products_raw` exista previamente. Esto se soluciona con el archivo `init_db.py`.
- Requiere que la carpeta RAW_DIR exista y contenga archivos JSONL.
- Requiere que la base de datos DuckDB esté inicializada.
- Requiere que las imágenes sean accesibles por URL.
"""

import os, io, time, pathlib, duckdb, requests, ujson, imagehash
from PIL import Image
from dotenv import load_dotenv

# ─────────────────── Configuración ────────────────────────
load_dotenv()
RAW_DIR = pathlib.Path(os.getenv("RAW_DIR", "raw_data"))   # carpeta con .jsonl
DB_PATH = pathlib.Path(os.getenv("DUCKDB_PATH", "db/dropi.db"))

RAW_DIR.mkdir(parents=True, exist_ok=True)

# ───────────────── Conexión a DuckDB ──────────────────────
con = duckdb.connect(DB_PATH.as_posix())

# ─────────────────── Utilidades ───────────────────────────
def download_image(url, timeout=10):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGB")

def compute_phash_signed(img):
    """phash 64-bit, convertido a BIGINT con signo"""
    h = int(str(imagehash.phash(img)), 16)
    return h - (1 << 64) if h >= (1 << 63) else h

def parse_int(v):
    try:
        return int(v)
    except Exception:
        return None

def parse_float(v):
    try:
        return float(v)
    except Exception:
        return None

def insert_record(rec, p_hash):
    sale_price      = parse_float(rec.get("sale_price"))
    suggested_price = parse_float(rec.get("suggested_price"))
    stock           = parse_int(rec.get("stock"))
    warehouse_id    = parse_int(rec.get("warehouse_id"))
    user_id         = parse_int(rec.get("user_id"))
    category_ids    = rec.get("category_ids") or []

    con.execute("""
        INSERT INTO products_raw
        (id, sku, name, sale_price, suggested_price,
         category_ids, user_id, user_name, stock, warehouse_id,
         image_url, phash, capture_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING
    """, (
        rec["id"], rec.get("sku"), rec.get("name"),
        sale_price, suggested_price, category_ids,
        user_id, rec.get("user_name"), stock, warehouse_id,
        rec.get("image_url"), p_hash, rec.get("capture_timestamp")
    ))

# ─────────────── Generador de líneas ──────────────────────
def stream_lines(dir_path):
    """Recorre todos los archivos raw_products_*.jsonl y los agota."""
    files = sorted(dir_path.glob("raw_products_*.jsonl"))
    for path in files:
        print(f"📂 Procesando {path.name}")
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                yield line
        print(f"✅ Terminado {path.name}")
    print("🏁 No quedan .jsonl por procesar. Cerrando loader…")

# ────────────────── Bucle principal ───────────────────────
print("🔄 Loader iniciado…")

inserted = 0
for line in stream_lines(RAW_DIR):
    rec = ujson.loads(line)

    # Evita duplicados por ID
    if con.execute("SELECT 1 FROM products_raw WHERE id = ?", (rec["id"],)).fetchone():
        continue

    try:
        img    = download_image(rec["image_url"])
        p_hash = compute_phash_signed(img)
    except Exception:
        p_hash = None

    insert_record(rec, p_hash)
    inserted += 1
    if inserted % 100 == 0:
        print(f"✅ {inserted} productos insertados hasta ahora")

# ─────────────────── Resumen final ────────────────────────
print(f"🏆 Loader finalizado. Total insertados: {inserted}")
con.close()
