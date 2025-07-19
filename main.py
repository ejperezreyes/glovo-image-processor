import os
import re
import time
import requests
import logging
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("glovo-scraper")

def download_restaurant_images(restaurant_url: str):
    OUTPUT_DIR   = "glovo_restaurant_images"
    SCROLL_STEPS = 8
    SCROLL_PAUSE = 1.0
    WAIT_TIMEOUT = 15

    log.info("🔧 Iniciando ChromeDriver")
    opts = Options()
    # opts.add_argument("--headless=new")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    driver  = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=opts)
    wait    = WebDriverWait(driver, WAIT_TIMEOUT)
    actions = ActionChains(driver)

    try:
        log.info("🌐 Abriendo %s", restaurant_url)
        driver.get(restaurant_url)
        time.sleep(2)

        # 1. Esperar y cerrar el banner de cookies
        try:
            log.info("🍪 Esperando banner de cookies/Usercentrics")
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-action-type='accept']")))
            btn.click()
            log.info("✅ Cookies aceptadas")
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "footer[data-testid='uc-footer']")))
        except Exception as e:
            log.warning("⚠️ No se encontró el banner de cookies: %s", e)

        # 2. Hacer scroll para que todos los productos estén visibles
        log.info("🔄 Scroll para cargar menú")
        for _ in range(SCROLL_STEPS):
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE)

        slug   = re.sub(r"[^0-9a-zA-Z_-]+", "_", restaurant_url.rstrip("/").split("/")[-1])
        folder = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(folder, exist_ok=True)
        log.info("📂 Carpeta creada: %s", folder)

        cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-test-id="product-row-content"]')
        log.info("🧾 Productos encontrados: %d", len(cards))

        for idx in tqdm(range(len(cards)), desc="📥 Descarga"):
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-test-id="product-row-content"]')
                card  = cards[idx]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                time.sleep(0.3)

                name_el = card.find_element(By.CSS_SELECTOR, "div.product-row__name span")
                name = name_el.text.strip()
                if not name:
                    continue

                actions.move_to_element(name_el).click().perform()
                time.sleep(0.5)

                # 3. Cerrar primer modal
                try:
                    log.info("❌ Cerrando modal intermedio")
                    close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.close-button[data-test-id='base-modal__close']")))
                    close_btn.find_element(By.XPATH, "..").click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[data-test-id='modal-window']")))
                    log.info("✅ Modal cerrado")
                except Exception as e:
                    log.error("❌ Error cerrando modal intermedio: %s", e)
                    continue

                # 4. Esperar imagen del modal final
                img = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "picture > img.magnifier__image")))
                src = img.get_attribute("src")
                if not src:
                    continue

                fname = re.sub(r"[^0-9a-zA-Z]+", "_", name).lower() + ".jpg"
                content = requests.get(src, timeout=10).content
                with open(os.path.join(folder, fname), "wb") as f:
                    f.write(content)

                # 5. Cerrar modal de producto final
                try:
                    svg2 = driver.find_element(By.CSS_SELECTOR, "svg.close-button[data-test-id='base-modal__close']")
                    svg2.find_element(By.XPATH, "..").click()
                    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div[data-test-id='modal-window']")))
                except:
                    actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.3)

            except Exception as e:
                log.warning("⚠️ Err producto %d: %s", idx, e)

        log.info("🎉 ¡Proceso completado! Imágenes en %s", folder)

    finally:
        driver.quit()

if __name__ == "__main__":
    download_restaurant_images("https://glovoapp.com/es/es/fuengirola/la-pizza-nostra-fuengirola/")