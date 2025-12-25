"""
Módulo principal de scraping para Dropi (Django Command).
"""
import os
import logging
import sys
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
from selenium.webdriver.remote.webdriver import WebDriver
from datetime import datetime
from urllib.parse import quote
import pathlib

# ─────── Cargar variables de entorno ───────
load_dotenv()

EMAIL       = os.getenv("DROPI_EMAIL")
PASSWORD    = os.getenv("DROPI_PASSWORD")
HEADLESS    = os.getenv("HEADLESS", "True").lower() in ("1", "true", "yes")
RAW_DIR_PATH = pathlib.Path(os.getenv("RAW_DIR", "raw_data"))
RAW_DIR_PATH.mkdir(parents=True, exist_ok=True)

# ─────── Configuración de Logs (Centralizada) ───────
# Creamos carpeta logs dentro del contenedor (montada a host)
LOG_DIR = pathlib.Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)

# Formatter bonito
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# 1. File Handler (Para visualización en Frontend)
file_handler = logging.FileHandler(LOG_DIR / "scraper.log", encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 2. Console Handler (Para Docker standard logs)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ─────── Helper Functions ───────

def jsonl_path():
    fname = f"raw_products_{datetime.utcnow():%Y%m%d}.jsonl"
    return RAW_DIR_PATH / fname

def build_driver() -> webdriver.Chrome:
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    
    # Docker friendly options
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # 1. Intentar usar driver del sistema (Docker)
    system_driver = os.environ.get("CHROMEDRIVER")
    if system_driver and os.path.exists(system_driver):
        logger.info(f"Using system chromedriver: {system_driver}")
        service = Service(system_driver)
    else:
        # 2. Fallback a webdriver_manager
        logger.info("Using webdriver_manager...")
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)

    return webdriver.Chrome(service=service, options=opts)

def login(driver: webdriver.Chrome, timeout: int = 60) -> bool:
    try:
        logger.info("1) Abriendo página de login…")
        driver.get("https://app.dropi.co/login")
        wait = WebDriverWait(driver, timeout)

        logger.info("2) Escribiendo credenciales...")
        email_el = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
        email_el.clear()
        email_el.send_keys(EMAIL)

        pwd_el = driver.find_element(By.NAME, "password")
        pwd_el.clear()
        pwd_el.send_keys(PASSWORD)
        pwd_el.send_keys(Keys.RETURN)

        logger.info("3) Esperando acceso (token o redirección)...")
        # Esperar validación: Token en Storage O Redirección exitosa
        wait.until(lambda d: d.execute_script("return !!localStorage.getItem('DROPI_token')") or "/dashboard" in d.current_url)
        
        driver.get_log("performance") # Limpiar logs
        logger.info("✅ Login exitoso")
        return True
    except Exception as e:
        import traceback
        logger.error(f"Login fallido: {type(e).__name__}: {e}")
        try:
            logger.error(f"URL Failed: {driver.current_url}")
            text = driver.find_element(By.TAG_NAME, "body").text[:300].replace('\n', ' ')
            logger.error(f"Pantalla: {text}")
        except: pass
        logger.error(traceback.format_exc())
        return False

def navigate_to_catalog(driver: webdriver.Chrome) -> None:
    logger.info("4) Navegando al catálogo (Modo Humano)...")
    time.sleep(5)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Intento 1: Navegación por menú
        # Buscamos "Productos" de forma más flexible
        prod_xpath = "//span[contains(text(), 'Productos')]"
        prod_el = wait.until(EC.element_to_be_clickable((By.XPATH, prod_xpath)))
        
        # Intentar click en el ancestro 'a' si existe, sino en el elemento mismo
        try:
            prod_el.find_element(By.XPATH, "./ancestor::a").click()
        except:
            prod_el.click()
            
        time.sleep(2) # Espera humana
        
        # Clic en "Catálogo"
        cat_xpath = "//a[contains(@href, '/dashboard/search') and contains(text(), 'Catálogo')]"
        cat_btn = wait.until(EC.element_to_be_clickable((By.XPATH, cat_xpath)))
        cat_btn.click()
        
        time.sleep(5)
        logger.info("🔍 Catálogo abierto (Navegación manual exitosa).")
        
    except Exception as e:
        # Log limpio sin stacktrace gigante
        err_msg = str(e).split('\n')[0]
        logger.warning(f"⚠️ No se pudo navegar el menú ({err_msg}). Abriendo URL directa para rescatar la sesión.")
        driver.get("https://app.dropi.co/dashboard/search")
        time.sleep(5)

def grab_new_products(driver: WebDriver, seen: set) -> list:
    new = []
    logs = driver.get_log("performance")
    for entry in logs: 
        try:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") != "Network.responseReceived": continue
            
            url = msg["params"]["response"]["url"]
            if "/api/products/v4/index" not in url: continue

            request_id = msg["params"]["requestId"]
            body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})["body"]
            payload = json.loads(body)
            objs = payload.get("objects") or payload.get("data", {}).get("objects", [])
            
            for p in objs:
                pid = p.get("id")
                if pid and pid not in seen:
                    seen.add(pid)
                    new.append(p)
        except:
            continue
    return new

def scroll_to_bottom(driver: WebDriver) -> None:
    driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
    time.sleep(1)
    # Scroll en contenedor interno si existe
    driver.execute_script("""
        var c = document.querySelector('.simplebar-content') || document.querySelector('.products-list');
        if (c) c.scrollTop = c.scrollHeight;
    """)

def click_show_more(driver: WebDriver) -> bool:
    try:
        btn = driver.find_element(By.XPATH, "//div[contains(text(),'Mostrar más productos')]")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except:
        return False

# ─────── Django Command ───────

class Command(BaseCommand):
    help = 'Scraper de Dropi (Daemon)'

    def handle(self, *args, **options):
        logger.info("🚀 SCRAPER DAEMON INICIADO (Modo Infinito)")
        
        while True:
            driver = None
            try:
                logger.info("🔄 Iniciando ciclo de scraping...")
                driver = build_driver()
                driver.execute_cdp_cmd("Network.enable", {})

                if not login(driver):
                    raise Exception("Login fallido")

                navigate_to_catalog(driver)
                
                seen = set()
                consecutive_no_button = 0

                with open(jsonl_path(), 'a', encoding='utf-8') as f:
                    while True:
                        nuevos = grab_new_products(driver, seen)
                        if nuevos:
                            for p in nuevos:
                                record = self.process_product(p)
                                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                                f.flush()
                            logger.info(f"📦 +{len(nuevos)} productos (Total: {len(seen)})")
                        
                        # Navegación
                        scroll_to_bottom(driver)
                        found = False
                        for _ in range(3):
                            if click_show_more(driver):
                                found = True
                                break
                            time.sleep(1)
                        
                        if not found:
                            consecutive_no_button += 1
                            if consecutive_no_button >= 5:
                                logger.info("🛑 Fin del catálogo o error. Reiniciando...")
                                break
                        else:
                            consecutive_no_button = 0
                        
                        # Reinicio preventivo de Chrome cada 1000 productos
                        if len(seen) % 1000 == 0 and len(seen) > 0:
                            logger.info(f"🔄 Reiniciando Chrome (mantenimiento preventivo - {len(seen)} productos procesados)...")
                            break
                        
                        time.sleep(1)

            except KeyboardInterrupt:
                logger.info("⏹️ Deteniendo scraper (Ctrl+C)...")
                break
            except Exception as e:
                error_msg = str(e)
                logger.error(f"💥 Error: {error_msg}")
                
                # Logging especial para errores conocidos
                if "tab crashed" in error_msg.lower():
                    logger.error("💥 Chrome crash detectado. Reiniciando navegador...")
                elif "session deleted" in error_msg.lower():
                    logger.error("💥 Sesión perdida. Reiniciando navegador...")
                
                logger.info("🔄 Reiniciando en 60 segundos...")
                time.sleep(60)
            finally:
                if driver:
                    try:
                        driver.quit()
                        logger.info("✅ Driver cerrado correctamente")
                    except Exception as e:
                        logger.warning(f"⚠️ Error al cerrar driver: {e}")
                    driver = None

    def process_product(self, p):
        # Lógica de extracción simplificada
        img_url = None
        gallery = p.get('gallery', [])
        if gallery:
            raw = gallery[0].get('urlS3') or gallery[0].get('url')
            if raw: img_url = f"https://d39ru7awumhhs2.cloudfront.net/{quote(raw, safe='/')}"

        wh_list = p.get('warehouse_product', [])
        wh_id = wh_list[0].get('warehouse_id') if wh_list else None
        stock = wh_list[0].get('stock', 0) if wh_list else 0

        return {
            "id": p.get('id'),
            "sku": p.get('sku'),
            "name": p.get('name', 'Sin Nombre'),
            "description": p.get('description', ''), # <-- Contexto para IA
            "type": p.get('type', 'SIMPLE'),
            "sale_price": p.get('sale_price'),
            "suggested_price": p.get('suggested_price'),
            "supplier": p.get('user', {}),
            "warehouse_id": wh_id,
            "stock": stock,
            "image_url": img_url,
            "categories": [c.get('name') for c in p.get('categories', [])],
            "capture_timestamp": datetime.utcnow().isoformat(),
            "raw_json": p
        }