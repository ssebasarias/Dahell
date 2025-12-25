"""
Módulo de carga ETL (Django Command).
"""
import os
import json
import logging
import pathlib
import sys
import time
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# ─────── Configuración de Logs ───────
LOG_DIR = pathlib.Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("loader")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

fh = logging.FileHandler(LOG_DIR / "loader.log", encoding='utf-8')
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Modificado para apuntar a la ruta correcta en Docker
RAW_DIR = pathlib.Path(os.getenv("RAW_DIR", "/app/raw_data"))

class Command(BaseCommand):
    help = 'ETL Loader Daemon'

    def handle(self, *args, **options):
        self.stdout.write("🚀 LOADER DAEMON INICIADO (Modo Infinito)")
        
        # Setup DB connection once (or Reconnect on fail)
        session = self.get_session()
        
        while True:
            try:
                files = list(RAW_DIR.glob("*.jsonl"))
                if not files:
                    logger.info("⏳ Sin archivos. Esperando 60s...")
                else:
                    for f in files:
                        self.process_file(f, session)
                
                logger.info("💤 Durmiendo 60 segundos...")
                time.sleep(60)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Error crítico: {e}")
                session = self.get_session() # Reconnect attempt
                time.sleep(60)

    def get_session(self):
        # Configuración DB
        user = os.getenv("POSTGRES_USER", "dahell_admin")
        pwd = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", "5433")
        dbname = os.getenv("POSTGRES_DB", "dahell_db")
        raw_db_url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{dbname}"
        
        engine = create_engine(raw_db_url, echo=False, connect_args={'client_encoding': 'utf8'})
        Session = sessionmaker(bind=engine)
        return Session()

    def process_file(self, filepath, session):
        logger.info(f"📂 Procesando: {filepath.name}")
        
        stats = {"total": 0, "inserted": 0, "updated": 0, "error": 0}
        error_types = {}  # Contador de tipos de error
        error_samples = []  # Primeros 10 errores para debugging
        success_samples = []  # Primeros 5 registros exitosos
        failed_data_samples = []  # Primeros 5 registros fallidos con sus datos
        
        # Estrategia de lectura robusta
        encoding_strategy = 'utf-8'
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(1024)
        except UnicodeDecodeError:
             encoding_strategy = 'latin-1'

        try:
            with open(filepath, 'r', encoding=encoding_strategy, errors='replace') as f:
                for line in f:
                    if not line.strip(): continue
                    stats["total"] += 1
                    
                    try:
                        record = json.loads(line)
                        was_insert = self.ingest_record(record, session)
                        session.commit()  # CRÍTICO: Commit inmediato por registro
                        
                        # Contar si fue INSERT o UPDATE
                        if was_insert:
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                        
                        # Guardar muestra de registros exitosos
                        if len(success_samples) < 5:
                            success_samples.append({
                                "id": record.get("id"),
                                "name": record.get("name", "")[:50],
                                "price": record.get("sale_price"),
                                "has_image": bool(record.get("image_url") or (record.get("gallery") and len(record.get("gallery", [])) > 0)),
                                "supplier_id": record.get("supplier", {}).get("id") if isinstance(record.get("supplier"), dict) else None
                            })
                        
                        # Logging por lotes (solo para mostrar progreso)
                        if (stats["inserted"] + stats["updated"]) % 100 == 0: 
                            self.print_batch_summary(filepath.name, stats)
                            
                    except Exception as e:
                        # Contar tipo de error
                        error_type = type(e).__name__
                        error_types[error_type] = error_types.get(error_type, 0) + 1
                        
                        # Guardar primeros 10 errores para análisis
                        if len(error_samples) < 10:
                            error_samples.append({
                                "type": error_type,
                                "message": str(e)[:200],
                                "record_id": record.get("id") if isinstance(record, dict) else None
                            })
                        
                        # Guardar datos completos de registros fallidos
                        if len(failed_data_samples) < 5:
                            failed_data_samples.append({
                                "id": record.get("id") if isinstance(record, dict) else None,
                                "name": record.get("name", "")[:50] if isinstance(record, dict) else None,
                                "price": record.get("sale_price") if isinstance(record, dict) else None,
                                "has_image": bool(record.get("image_url") or (record.get("gallery") and len(record.get("gallery", [])) > 0)) if isinstance(record, dict) else False,
                                "supplier_id": record.get("supplier", {}).get("id") if isinstance(record, dict) and isinstance(record.get("supplier"), dict) else None,
                                "error": str(e)[:100]
                            })
                        
                        stats["error"] += 1
                        session.rollback()
                        # Ya no necesitamos commit aquí porque cada registro exitoso
                        # hace su propio commit, iniciando automáticamente una nueva transacción

            session.commit()
            self.print_batch_summary(filepath.name, stats, final=True)
            
            # Loguear resumen de errores
            if error_types:
                logger.warning(f"\n⚠️  RESUMEN DE ERRORES en {filepath.name}:")
                for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    logger.warning(f"   - {err_type}: {count} ocurrencias")
                
                if error_samples:
                    logger.warning(f"\n🔍 PRIMEROS {len(error_samples)} ERRORES (para debugging):")
                    for i, err in enumerate(error_samples, 1):
                        logger.warning(f"   {i}. [{err['type']}] ID={err['record_id']}: {err['message']}")
                
                # Loguear comparación de datos
                if success_samples:
                    logger.info(f"\n✅ MUESTRA DE REGISTROS EXITOSOS ({len(success_samples)}):")
                    for i, rec in enumerate(success_samples, 1):
                        logger.info(f"   {i}. ID={rec['id']}, Name='{rec['name']}', Price={rec['price']}, Image={rec['has_image']}, Supplier={rec['supplier_id']}")
                
                if failed_data_samples:
                    logger.warning(f"\n❌ MUESTRA DE REGISTROS FALLIDOS ({len(failed_data_samples)}):")
                    for i, rec in enumerate(failed_data_samples, 1):
                        logger.warning(f"   {i}. ID={rec['id']}, Name='{rec['name']}', Price={rec['price']}, Image={rec['has_image']}, Supplier={rec['supplier_id']}")
                        logger.warning(f"      Error: {rec['error']}")

        except Exception as e:
            logger.error(f"❌ Error fatal en archivo {filepath.name}: {e}")

    def print_batch_summary(self, filename, stats, final=False):
        """Imprime una tabla bonita en el log"""
        icon = "🏁" if final else "📦"
        status = "COMPLETADO" if final else "EN PROGRESO"
        
        total_procesados = stats['inserted'] + stats['updated']
        
        msg = (
            f"\n{icon} Lote {filename} [{status}]\n"
            f"✅ Nuevos insertados: {stats['inserted']}\n"
            f"🔄 Actualizados (duplicados): {stats['updated']}\n"
            f"📊 Total procesados: {total_procesados}\n"
            f"⚠️  Omitidos (Errores): {stats['error']}\n"
            f"----------------------------------------"
        )
        logger.info(msg)


    def ingest_record(self, data, session):
        # --- 1. Bodega ---
        wh_id = data.get("warehouse_id")
        if wh_id:
            try:
                session.execute(text("""
                    INSERT INTO warehouses (warehouse_id, first_seen_at, last_seen_at) 
                    VALUES (:wid, NOW(), NOW())
                    ON CONFLICT (warehouse_id) DO UPDATE SET last_seen_at = NOW()
                """), {"wid": wh_id})
            except Exception:
                pass 

        # --- 2. Proveedor ---
        supp = data.get("supplier", {})
        if supp and supp.get("id"):
            p_name = None
            if isinstance(supp.get("plan"), dict):
                p_name = supp.get("plan", {}).get("name")
            else:
                p_name = supp.get("plan_name")

            session.execute(text("""
                INSERT INTO suppliers (supplier_id, name, store_name, plan_name, is_verified, created_at, updated_at)
                VALUES (:sid, :name, :store, :plan, FALSE, NOW(), NOW())
                ON CONFLICT (supplier_id) DO UPDATE
                SET name = EXCLUDED.name, store_name = EXCLUDED.store_name, plan_name = EXCLUDED.plan_name, updated_at = NOW()
            """), {
                "sid": supp.get("id"),
                "name": str(supp.get("name") or "")[:255],
                "store": str(supp.get("store_name") or "")[:255],
                "plan": str(p_name or "")[:100]
            })

        # --- 3. Producto ---
        prod_id = data.get("id")
        was_insert = False
        
        if prod_id:
            # Verificar si el producto ya existe
            result = session.execute(text("""
                SELECT 1 FROM products WHERE product_id = :pid
            """), {"pid": prod_id})
            
            product_exists = result.fetchone() is not None
            
            # Insertar o actualizar
            session.execute(text("""
                INSERT INTO products (
                    product_id, supplier_id, sku, title, description,
                    sale_price, suggested_price, product_type, 
                    url_image_s3, is_active, created_at, updated_at
                ) VALUES (
                    :pid, :sid, :sku, :title, :desc,
                    :price, :sugg, :type, 
                    :img, TRUE, NOW(), NOW()
                )
                ON CONFLICT (product_id) DO UPDATE
                SET sale_price = EXCLUDED.sale_price,
                    suggested_price = EXCLUDED.suggested_price,
                    description = COALESCE(EXCLUDED.description, products.description),
                    updated_at = NOW(),
                    url_image_s3 = COALESCE(EXCLUDED.url_image_s3, products.url_image_s3)
            """), {
                "pid": prod_id,
                "sid": supp.get("id") if supp else None,
                "sku": str(data.get("sku") or "")[:100],
                "title": data.get("name") or "Sin Nombre",
                "desc": data.get("description"),
                "price": data.get("sale_price"),
                "sugg": data.get("suggested_price"),
                "type": str(data.get("type") or "")[:50],
                "img": data.get("image_url") 
                       or (data.get("gallery") and data.get("gallery")[0].get("urlS3"))
                       or (data.get("gallery") and data.get("gallery")[0].get("url"))
            })
            
            # Si no existía antes, fue un INSERT
            was_insert = not product_exists

            # --- 4. Stock ---
            if wh_id:
                try:
                    qty = int(data.get("stock") or 0)
                    session.execute(text("""
                        INSERT INTO product_stock_log (product_id, warehouse_id, stock_qty)
                        VALUES (:pid, :wid, :qty)
                    """), {"pid": prod_id, "wid": wh_id, "qty": qty})
                except: pass
        
        return was_insert
