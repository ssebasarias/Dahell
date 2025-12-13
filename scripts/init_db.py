# init_db.py — esquema listo para enriquecer y clusterizar (compatible)
import os
import pathlib
import duckdb
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "db/dropi.db")

db_file = pathlib.Path(DB_PATH)
db_file.parent.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(db_file.as_posix())

# 1) Ingesta base
con.execute("""
CREATE TABLE IF NOT EXISTS products_raw (
    id              BIGINT PRIMARY KEY,
    sku             VARCHAR,
    name            VARCHAR,
    sale_price      DOUBLE,
    suggested_price DOUBLE,
    category_ids    BIGINT[],
    user_id         BIGINT,
    user_name       VARCHAR,
    stock           INTEGER,
    warehouse_id    BIGINT,
    image_url       VARCHAR,
    phash           BIGINT,
    clip_vec        BLOB,
    capture_ts      TIMESTAMP
);
""")

#-- Derivados opcionales para consumo rápido/reportes
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS suggested_price_ext DOUBLE;")
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS price_p25 DOUBLE;")
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS price_p50 DOUBLE;")  # mediana
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS price_p75 DOUBLE;")
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS image_source VARCHAR;")
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS last_enriched_ts TIMESTAMP;")
con.execute("ALTER TABLE products_raw ADD COLUMN IF NOT EXISTS enrich_confidence DOUBLE;")

# 2) Observaciones de precio (histórico)
con.execute("""
CREATE TABLE IF NOT EXISTS market_prices (
    product_id       BIGINT,          -- FK lógico a products_raw.id
    source           VARCHAR,         -- meli, falabella, exito, serpapi_google, etc.
    title_normalized VARCHAR,
    price            DOUBLE CHECK (price >= 0),
    currency         VARCHAR,         -- 'COP', etc.
    product_url      VARCHAR,
    image_url_source VARCHAR,
    captured_at      TIMESTAMP,       -- cuándo se vio el precio
    confidence       DOUBLE DEFAULT 0.5,  -- 0..1 score del match
    PRIMARY KEY (product_id, source, product_url, captured_at)
);
""")

# Vista de métricas por producto (p25/p50/p75, n, last_seen)
con.execute("""
CREATE VIEW IF NOT EXISTS product_price_stats AS
SELECT
  product_id,
  COUNT(*)                     AS n,
  quantile(price, 0.25)        AS p25,
  median(price)                AS p50,
  quantile(price, 0.75)        AS p75,
  MAX(captured_at)             AS last_seen,
  AVG(confidence)              AS avg_confidence
FROM market_prices
WHERE price IS NOT NULL AND confidence >= 0.5
GROUP BY product_id;
""")

# 3) Candidatas de imagen (para rellenar nulos y elegir canónica)
con.execute("""
CREATE TABLE IF NOT EXISTS product_assets (
    product_id  BIGINT,
    image_url   VARCHAR,
    source      VARCHAR,                 -- 'dropi', 'cse', 'bing', dominio, etc.
    status      VARCHAR DEFAULT 'ok',    -- ok/404/mismatch
    phash       BIGINT,
    dhash       BIGINT,
    width       INTEGER,
    height      INTEGER,
    mime        VARCHAR,
    bytes_sha1  VARCHAR,                 -- para duplicados exactos
    download_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, image_url)
);
""")

# 4) Clusterización (mismo producto con nombre/foto distinta)
con.execute("""
CREATE TABLE IF NOT EXISTS product_clusters (
    cluster_id   BIGINT PRIMARY KEY,
    canonical_id BIGINT,        -- product_id representativo del cluster
    num_sellers  INTEGER,
    last_seen    TIMESTAMP
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id       BIGINT,
    product_id       BIGINT,
    linked_ts        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    phash_distance   INTEGER,
    text_similarity  DOUBLE,
    clip_similarity  DOUBLE,
    PRIMARY KEY (cluster_id, product_id)
);
""")

# (Compatibilidad si ya la usas)
con.execute("""
CREATE TABLE IF NOT EXISTS supplier_listing (
    cluster_id   BIGINT,
    supplier_id  BIGINT,
    first_seen   TIMESTAMP,
    last_seen    TIMESTAMP,
    sku          VARCHAR,
    PRIMARY KEY(cluster_id, supplier_id)
);
""")

con.close()
print(f"✅ Base creada/actualizada en {DB_PATH}")
