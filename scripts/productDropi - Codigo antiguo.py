"""
Módulo principal de scraping para Dropi.
----------------------------------------
Este script usa Selenium para:
  1. Iniciar sesión en Dropi usando credenciales de .env.
  2. Mantener abierta la sesión y exponer un driver configurado.
  3. Más adelante se añadirá la lógica de scroll / XHR.

Responsabilidades de este archivo:
- Leer configuración (.env).
- Construir y devolver un webdriver listo para usar.
- No realizar el parsing de productos ni almacenamiento final.
"""

import os
import logging
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
import csv
import traceback
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import requests
from urllib.parse import quote
import pathlib


# ─────── Cargar variables de entorno ───────
load_dotenv()  # busca automáticamente .env en la carpeta raíz

EMAIL       = os.getenv("DROPI_EMAIL")
PASSWORD    = os.getenv("DROPI_PASSWORD")
HEADLESS    = os.getenv("HEADLESS", "True").lower() in ("1", "true", "yes")
MAX_PRODUCTS= int(os.getenv("MAX_PRODUCTS", 200))
OUT_CSV     = os.getenv("OUT_CSV", "catalogo_dropi.csv")
RAW_DIR = os.getenv("RAW_DIR", "raw_data")

RAW_DIR_PATH = pathlib.Path(RAW_DIR)
RAW_DIR_PATH.mkdir(parents=True, exist_ok=True)
# ─────── manejo de jsonl ───────
def jsonl_path():
    # ⇩  rotación DIARIA (YYYYMMDD).  
    #     Si quieres HORARIA usa %Y%m%d_%H
    fname = f"raw_products_{datetime.utcnow():%Y%m%d}.jsonl"
    return RAW_DIR_PATH / fname
# ─────── Logging básico ───────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ───────────── Funciones de configuración ─────────────

def build_driver() -> webdriver.Chrome:
    """
    Construye y devuelve un objeto Selenium WebDriver para Chrome,
    configurado en modo headless (si HEADLESS=True) y con capacidad
    de capturar logs de red.

    Configuraciones clave:
    - window-size: 1920×1080
    - loggingPrefs: performance (para capturar XHR via CDP)
    - headless: según la variable de entorno HEADLESS

    Returns:
        webdriver.Chrome: instancia lista para navegar.
    """
    opts = Options()

    if HEADLESS:
        opts.add_argument("--headless=new")
        logger.debug("Iniciando Chrome en modo headless")

    # Asegurarnos de un tamaño suficiente para que aparezcan todos los elementos
    opts.add_argument("--window-size=1920,1080")

    # Habilitar captura de logs de red (Performance)
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # Instala (o reutiliza) el ChromeDriver adecuado a tu Chrome
    driver_path = ChromeDriverManager().install()
    service     = Service(driver_path)

    logger.info(f"ChromeDriver instalado en: {driver_path}")

    driver = webdriver.Chrome(service=service, options=opts)
    logger.info("WebDriver creado correctamente")

    return driver

# Al ejecutar directamente, solo probamos la creación del driver
if __name__ == "__main__":
    drv = build_driver()
    drv.quit()
    logger.info("Driver inicializado y cerrado con éxito")


# ───────────── Función de login ─────────────

def login(driver: webdriver.Chrome, timeout: int = 30) -> None:
    """
    Realiza el login en Dropi usando las credenciales cargadas desde .env.
    Tras completar, deja una sesión válida y limpia los logs de red previos.

    Args:
        driver (webdriver.Chrome): Instancia del WebDriver.
        timeout (int): Tiempo máximo a esperar por cada paso.

    Raises:
        TimeoutException: Si algún elemento no aparece en el tiempo dado.
    """
    logger.info("1) Abriendo página de login…")
    driver.get("https://app.dropi.co/login")

    wait = WebDriverWait(driver, timeout)

    # 2) Esperar campo email y escribirlo
    logger.info("2) Esperando campo 'email' y escribiendo…")
    email_el = wait.until(EC.visibility_of_element_located((By.NAME, "email")))
    email_el.clear()
    email_el.send_keys(EMAIL)

    # 3) Escribir contraseña y enviar
    logger.info("3) Escribiendo contraseña y enviando formulario…")
    pwd_el = driver.find_element(By.NAME, "password")
    pwd_el.clear()
    pwd_el.send_keys(PASSWORD)
    pwd_el.send_keys(Keys.RETURN)

    # 4) Esperar a que Angular o React guarde el token en localStorage
    logger.info("4) Esperando token en localStorage…")
    wait.until(lambda d: d.execute_script(
        "return !!localStorage.getItem('DROPI_token')"
    ))

    # Opcional: limpiar logs previos para empezar de cero
    driver.get_log("performance")
    logger.info("✅ Login exitoso y logs de red limpiados")


# ───────── Navegación hasta el catálogo ─────────

def navigate_to_catalog(driver: webdriver.Chrome) -> None:
    """
    Tras el login, navega el menú lateral para abrir la sección
    'Productos' y dentro de ella 'Catálogo'. Usa esperas dinámicas
    y sleeps mínimos para adaptarse a la lentitud de la SPA.

    Args:
        driver (webdriver.Chrome): Instancia del WebDriver en sesión.
    """
    # A veces el sidebar tarda en renderizarse
    logger.info("5) Esperando que cargue el sidebar…")
    time.sleep(5)

    wait = WebDriverWait(driver, 20)

    # 6) Clic en "Productos" para desplegar el submenú
    logger.info("6) Haciendo clic en 'Productos'…")
    prod_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//span[normalize-space()='Productos']/ancestor::a"
    )))
    prod_btn.click()
    time.sleep(1)

    # 7) Clic en "Catálogo" dentro del submenú
    logger.info("7) Haciendo clic en 'Catálogo'…")
    cat_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//a[@href='/dashboard/search' and normalize-space()='Catálogo']"
    )))
    cat_btn.click()

    # 8) Esperar brevemente a que aparezca la lista de productos
    logger.info("8) Esperando a que cargue la vista de catálogo…")
    time.sleep(5)

    # Verificación final opcional: existe el contenedor de productos
    exists = driver.execute_script(
        "return !!document.querySelector('.products-list, .simplebar-content')"
    )
    if not exists:
        logger.warning("No se detectó el contenedor de productos tras la navegación.")
    else:
        logger.info("🔍 Navegación al catálogo completada exitosamente.")


# captura de XHR, scroll y escritura incremental
"""
En esta sección se implementan:
  - grab_new_products: extrae nuevos productos de los logs de red.
  - scroll_to_bottom: baja suavemente hasta el final del contenedor.
  - click_show_more: pulsa el botón “Mostrar más productos” si existe.
  - main: orquesta el flujo completo y escribe incrementalmente en CSV.
"""

# ─────────── Extracción de nuevos productos ───────────

def grab_new_products(driver: WebDriver, seen: set) -> list:
    """
    Lee los logs de red (performance) y extrae respuestas XHR a /api/products/v4/index.
    Filtra por 'id' para devolver solo productos no procesados.

    Args:
        driver (WebDriver): Navegador con CDP habilitado (Network.enable).
        seen (set): Conjunto de IDs ya registrados.

    Returns:
        List[dict]: Lista de nuevos objetos de producto.
    """
    new = []
    for entry in driver.get_log("performance"): 
        try:
            msg = json.loads(entry["message"])["message"]
        except (KeyError, ValueError):
            continue

        # Filtrar solo eventos de respuesta
        if msg.get("method") != "Network.responseReceived":
            continue

        url = msg["params"]["response"]["url"]
        if "/api/products/v4/index" not in url:
            continue

        request_id = msg["params"]["requestId"]
        try:
            # Obtener cuerpo mediante CDP
            body = driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )["body"]
            payload = json.loads(body)
            # Soporta ambos formatos: raíz 'objects' o bajo 'data'
            objs = payload.get("objects") or payload.get("data", {}).get("objects", [])
        except Exception:
            continue

        for p in objs:
            pid = p.get("id")
            if pid and pid not in seen:
                seen.add(pid)
                new.append(p)

    return new


# ───────────── Scroll hasta el fondo ─────────────

def scroll_to_bottom(driver: WebDriver) -> None:
    """
    Ejecuta un scroll incremental hacia el fondo del contenedor principal
    para disparar la carga de más productos.
    """
    # scroll en ventana principal
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(0.5)

    # scroll en contenedor específico (SPA)
    driver.execute_script(
        """
        var c = document.querySelector('.simplebar-content')
              || document.querySelector('.products-list')
              || document.querySelector('main');
        if (c) c.scrollTop = c.scrollHeight;
        """
    )
    time.sleep(1)


# ───────── Pulsar botón "Mostrar más" ─────────

def click_show_more(driver: WebDriver) -> bool:
    """
    Intenta encontrar y pulsar el botón "Mostrar más productos".

    Returns:
        bool: True si hizo clic, False si no existe el botón.
    """
    try:
        btn = driver.find_element(
            By.XPATH,
            "//div[contains(text(),'Mostrar más productos')]"
        )
        # Llevamos el botón al centro y clicamos
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception:
        return False

# ───────── Manejo de imagenes ─────────
IMG_HOST = "https://d39ru7awumhhs2.cloudfront.net"

def build_image_url(path: str) -> str:
   return f"{IMG_HOST}/{quote(path, safe='/')}"


# ───────────── Orquestador principal ─────────────

def main():
    """
    Flujo completo:
      1. Crea driver y habilita CDP Network.
      2. Login y navegación al catálogo.
      3. Abre JSONL en modo append.
      4. Bucle: captura nuevos XHR, escribe registro JSONL y repite scroll+clic.
      5. Finaliza al no haber más botón.
    """
    driver = None
    try:
        driver = build_driver()
        driver.execute_cdp_cmd("Network.enable", {})

        login(driver)
        driver.get_log("performance")
        navigate_to_catalog(driver)

        seen = set()

        with open(jsonl_path(), 'a', encoding='utf-8') as jsonl_file:
            while True:
                nuevos = grab_new_products(driver, seen)
                if nuevos:
                    for p in nuevos:
                        # Campos clave para dedupe y análisis
                        prod_id = p.get('id', '')
                        sku = p.get('sku', '')
                        timestamp = datetime.utcnow().isoformat()
                        warehouse_id = p.get('warehouse_id', '')
                        stock = p.get('stock', '')

                        # Categorías y sus IDs
                        cats = p.get('categories', [])
                        cat_ids = [c.get('id') for c in cats]

                        # Proveedor
                        user = p.get('user', {})
                        user_id = user.get('id', '')
                        user_name = user.get('name', '')

                        # URL de imagen principal
                        gal = p.get('gallery', [])
                        raw_path = None
                        if gal:
                            raw_path = gal[0].get('urlS3') or gal[0].get('url')  # preferimos urlS3

                        img_url = build_image_url(raw_path) if raw_path else ''
                        
                        # Construir registro JSON
                        record = {
                            "id": prod_id,
                            "sku": sku,
                            "capture_timestamp": timestamp,
                            "warehouse_id": warehouse_id,
                            "stock": stock,
                            "category_ids": cat_ids,
                            "categories": cats,
                            "user_id": user_id,
                            "user_name": user_name,
                            "name": p.get('name', ''),
                            "sale_price": p.get('sale_price', ''),
                            "suggested_price": p.get('suggested_price', ''),
                            "image_url": img_url
                        }
                        jsonl_file.write(json.dumps(record, ensure_ascii=False) + '\n')
                        jsonl_file.flush()

                    logger.info(f"📦 Añadidos {len(nuevos)} productos (total único: {len(seen)})")

                # Cargar más productos
                scroll_to_bottom(driver)
                if not click_show_more(driver):
                    logger.info("🔔 No hay más productos")
                    break
                time.sleep(1)

    except Exception:
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            logger.info("🔒 Navegador cerrado")


if __name__ == "__main__":
    main()