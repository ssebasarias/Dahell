import os
from dotenv import load_dotenv

load_dotenv()

# Credenciales Dropi
DROPI_EMAIL    = os.getenv("DROPI_EMAIL")
DROPI_PASSWORD = os.getenv("DROPI_PASSWORD")

# Rutas
RAW_JSONL      = "raw_data/raw_products.jsonl"
CATALOG_CSV    = "output/catalogo_dropi.csv"
DB_PATH        = "db/dropi.db"

# Parámetros
PAGE_LIMIT     = 100
HEADLESS       = True