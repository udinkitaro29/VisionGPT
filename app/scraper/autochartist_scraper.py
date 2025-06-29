# app/scraper/autochartist_scraper.py
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional

# --- PERUBAHAN: Aktifkan level DEBUG untuk melihat semua log ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# --- AKHIR PERUBAHAN ---
logger = logging.getLogger(__name__)

# BASE_IFRAME_URL diambil dari config di versi production, ini untuk tes mandiri
BASE_IFRAME_URL = "https://dclb.autochartist.com/to/?user=adspraktek@gmail.com&account_type=LIVE&broker_id=916&token=9b140f3c48378a37dcad6cef20c1db6d&expire=1751436376&locale=en_GB&page_limit=6&result_limit=6&css=https://broker-resources.autochartist.com/css/component_container/916-to-app.css&layout=horizontal&gtmID=GTM-WWN2DSV#/results"
TARGET_CATEGORIES = ["Forex", "Commodities", "Cryptos"]

def setup_driver():
    # ... (Fungsi ini tidak diubah)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless'); options.add_argument('--disable-gpu'); options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    base_chromedriver_dir = r"C:\Users\KNRP\Desktop\TradingSignalBot\chromedriver-win64\chromedriver-win64"
    chromedriver_path = os.path.join(base_chromedriver_dir, "chromedriver.exe")
    if not os.path.exists(chromedriver_path):
        logger.error(f"ChromeDriver.exe tidak ditemukan di path: {chromedriver_path}"); return None
    try:
        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        logger.info(f"WebDriver Chrome berhasil diinisialisasi dengan path manual.")
        return driver
    except Exception as e:
        logger.error(f"Gagal menginisialisasi WebDriver: {e}", exc_info=True); return None

def clean_text(text: Optional[str]) -> str:
    # ... (Fungsi ini tidak diubah)
    if text: return " ".join(text.strip().split())
    return ""

def extract_price_value(value_text: Optional[str]) -> Optional[float]:
    # ... (Fungsi ini tidak diubah)
    if value_text:
        match = re.search(r':\s*([\d.]+)', value_text)
        if match:
            try: return float(match.group(1))
            except ValueError: logger.warning(f"Tidak bisa konversi harga ke float dari: '{value_text}'")
    return None

def extract_expiry_datetime(expiry_text_raw: Optional[str]) -> str:
    # ... (Fungsi ini tidak diubah)
    if expiry_text_raw:
        match = re.search(r'(\d{1,2}/\d{1,2}\s+\d{2}:\d{2})', expiry_text_raw)
        if match: return match.group(1)
    return ""

def parse_signal_levels(panel: BeautifulSoup, panel_index: int) -> Dict[str, any]:
    # ... (Fungsi ini tidak diubah)
    levels = {"entry_price": None, "take_profit": None, "stop_loss": None, "target_period": ""}
    levels_container = panel.select_one('div.row[ng-if="item.data.signal_levels"]')
    if not levels_container:
        logger.debug(f"Panel #{panel_index}: Kontainer level tidak ditemukan.")
        return levels
    h5_elements = levels_container.select('h5.list-group-item-heading.ng-scope[ng-if]')
    for h5 in h5_elements:
        spans = h5.select('span.ng-binding')
        if len(spans) == 2:
            label_text = clean_text(spans[0].text).lower()
            value_text_raw = clean_text(spans[1].text)
            if "entry level" in label_text: levels["entry_price"] = extract_price_value(value_text_raw)
            elif "stop-loss" in label_text: levels["stop_loss"] = extract_price_value(value_text_raw)
            elif "target level" in label_text: levels["take_profit"] = extract_price_value(value_text_raw)
            elif "target period" in label_text:
                period_match = re.search(r':\s*(.+)', value_text_raw)
                if period_match: levels["target_period"] = period_match.group(1).strip()
        elif len(spans) == 1 and "entry level" in clean_text(spans[0].text).lower():
              value_text_raw = clean_text(spans[0].text)
              if "entry level" in value_text_raw.lower():
                  levels["entry_price"] = extract_price_value(value_text_raw.replace("Entry Level",""))
    return levels

def scrape_page_signals(soup: BeautifulSoup) -> List[Dict]:
    page_signals_data: List[Dict] = []
    signal_panels = soup.select('div.list-group-item')
    logger.info(f"Ditemukan {len(signal_panels)} panel sinyal di halaman ini.")
    if not signal_panels: logger.warning("Tidak ada panel sinyal ('div.list-group-item') di halaman ini.")

    for i, panel in enumerate(signal_panels):
        panel_idx_for_log = i + 1
        logger.debug(f"Memproses panel #{panel_idx_for_log} di halaman saat ini")
        try:
            pair, interval, pattern_name, pattern_type, age = "", "", "", "", ""
            short_description, image_url, expiry_datetime_val = "", "", ""
            symbol_row = panel.select_one('h4.symbol-row')
            if symbol_row:
                pair = clean_text(symbol_row.select_one('span.symbol').text if symbol_row.select_one('span.symbol') else "")
                interval = clean_text(symbol_row.select_one('span.interval').text if symbol_row.select_one('span.interval') else "")
            pattern_info_row = panel.select_one('h5.pattern-row')
            if pattern_info_row:
                pattern_name = clean_text(pattern_info_row.select_one('span.pattern').text if pattern_info_row.select_one('span.pattern') else "")
                pattern_type = clean_text(pattern_info_row.select_one('span.pattern-type').text if pattern_info_row.select_one('span.pattern-type') else "")
                age = clean_text(pattern_info_row.select_one('small.time').text if pattern_info_row.select_one('small.time') else "")
            levels_data = parse_signal_levels(panel, panel_idx_for_log)
            entry_price, take_profit, stop_loss, target_period = levels_data["entry_price"], levels_data["take_profit"], levels_data["stop_loss"], levels_data["target_period"]
            description_element = panel.select_one('div.list-group-item-text div.analysis-text div.well.well-sm > span.ng-binding')
            if description_element: short_description = clean_text(description_element.text)
            else: logger.debug(f"Panel #{panel_idx_for_log}: Deskripsi singkat tidak ditemukan.")
            image_element = panel.select_one('img.chart.pattern-img')
            if image_element: image_url = image_element.get('actual-src') or image_element.get('src') or ""
            all_rows_in_panel = panel.select('div.row')
            if all_rows_in_panel:
                expiry_row_candidate = all_rows_in_panel[-1] 
                expiry_element = expiry_row_candidate.select_one('div.pull-right > span.ng-binding[ng-if="item.data.expires_at"]')
                if expiry_element: expiry_datetime_val = extract_expiry_datetime(clean_text(expiry_element.text))
            
            raw_desc_parts = [f"Aset: {pair} (TF{interval}).", f"Pola: {pattern_name}{f' ({pattern_type})' if pattern_type else ''}.", f"Usia: {age}.", f"Deskripsi: {short_description}.", f"Expiry: {expiry_datetime_val}."]
            raw_description = " ".join(filter(None, raw_desc_parts)) or "Data tidak lengkap."
            
            if pair:
                signal = {
                    "pair": pair.upper(), "timeframe": interval, "pattern_name": pattern_name,
                    "pattern_type": pattern_type, "pattern_age": age, "entry_price": entry_price,
                    "take_profit": take_profit, "stop_loss": stop_loss, "target_period": target_period,
                    "expiry_datetime": expiry_datetime_val, "short_description": short_description,
                    "raw_description": raw_description, "image_url": image_url,
                    "source": "Autochartist", "direction": "UNKNOWN" 
                }
                page_signals_data.append(signal)
            else:
                logger.warning(f"Panel #{panel_idx_for_log} di halaman ini tidak memiliki 'pair', dilewati.")
        
        # --- PERUBAHAN UTAMA: TAMBAHKAN BLOK DEBUG DI SINI ---
        except Exception as e:
            logger.error(f"GAGAL MEMPROSES PANEL #{panel_idx_for_log} DI HALAMAN INI: {e}", exc_info=True)
            try:
                # Coba ambil HTML dari panel untuk debug
                panel_html = str(panel)
                logger.debug(f"HTML DARI PANEL YANG GAGAL:\n{panel_html}")
            except Exception as html_e:
                logger.error(f"Gagal mendapatkan HTML dari panel yang error: {html_e}")
        # --- AKHIR PERUBAHAN ---
                
    return page_signals_data

def scrape_one_category_all_pages(driver: webdriver.Chrome, category_url: str) -> List[Dict]:
    """Mengambil semua sinyal dari semua halaman untuk satu kategori market."""
    all_category_signals: List[Dict] = []
    current_page_num = 1
    
    logger.info(f"Navigasi ke URL kategori: {category_url}")
    driver.get(category_url)

    while True:
        category_name = category_url.split('#/results/')[-1] if '#/results/' in category_url else "UnknownCategory"
        logger.info(f"Memulai scrape untuk Kategori: {category_name}, Halaman: {current_page_num}")
        try:
            WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.list-group-item")))
            logger.info(f"Panel sinyal ditemukan di halaman {current_page_num}.")
            time.sleep(3)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            signals_on_this_page = scrape_page_signals(soup)
            
            if not signals_on_this_page and current_page_num > 1:
                logger.info(f"Tidak ada sinyal ditemukan di halaman {current_page_num}, anggap akhir paginasi.")
                break
            
            all_category_signals.extend(signals_on_this_page)
            
            if not signals_on_this_page and current_page_num == 1:
                logger.warning(f"Tidak ada sinyal ditemukan di halaman PERTAMA untuk kategori {category_name}.")

            try:
                next_page_button_xpath = "//ul[contains(@class,'pagination')]//li[contains(@class,'clickable') and not(contains(@class,'disabled'))]//a[./span[normalize-space(text())='>']]"
                next_page_button = driver.find_element(By.XPATH, next_page_button_xpath)
                logger.info(f"Tombol 'Next Page' ditemukan. Mengklik ke halaman {current_page_num + 1}...")
                driver.execute_script("arguments[0].click();", next_page_button)
                current_page_num += 1
                time.sleep(2) 
            except NoSuchElementException:
                logger.info(f"Akhir paginasi untuk kategori {category_name}.")
                break
            except Exception as e_page:
                logger.error(f"Error saat paginasi untuk {category_name}: {e_page}", exc_info=True)
                break
        except TimeoutException:
            logger.warning(f"Timeout saat menunggu panel sinyal di halaman {current_page_num} untuk {category_name}.")
            break
        except Exception as e_scrape_page:
            logger.error(f"Error saat scrape halaman {current_page_num} untuk {category_name}: {e_scrape_page}", exc_info=True)
            break
            
    return all_category_signals

def scrape_all_autochartist_data(categories: List[str] = TARGET_CATEGORIES) -> List[Dict]:
    # ... (Fungsi ini tidak diubah)
    driver = setup_driver()
    if not driver: return []
    all_signals: List[Dict] = []
    try:
        for category in categories:
            category_url_fragment = f"#/results/{category.replace(' ', '%20')}"
            full_category_url = BASE_IFRAME_URL.split('#/results')[0] + category_url_fragment
            logger.info(f"--- Memulai scraping untuk kategori: {category} ({full_category_url}) ---")
            category_signals = scrape_one_category_all_pages(driver, full_category_url)
            all_signals.extend(category_signals)
            logger.info(f"--- Selesai scraping untuk kategori: {category}, total ditemukan {len(category_signals)} sinyal ---")
            if category_signals:
                logger.info(f"Contoh sinyal pertama dari {category}: {str(category_signals[0])[:200]}...")
            if category != categories[-1]:
                logger.info("Memberi jeda 5 detik sebelum scrape kategori berikutnya...")
                time.sleep(5) 
    except Exception as e:
        logger.error(f"Error saat scraping semua kategori: {e}", exc_info=True)
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver ditutup setelah semua kategori selesai.")
    return all_signals

if __name__ == '__main__':
    # ... (Bagian ini tidak diubah)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info(f"Memulai scraping manual untuk kategori: {TARGET_CATEGORIES}...")
    signals = scrape_all_autochartist_data()
    if signals:
        logger.info(f"TOTAL BERHASIL MENDAPATKAN {len(signals)} SINYAL DARI SEMUA KATEGORI.")
        # Opsi untuk print semua detail sinyal yang berhasil di-scrape
        # for i, signal_item in enumerate(signals):
        #     print(f"\n--- Sinyal #{i+1} ---")
        #     print(json.dumps(signal_item, indent=2))
    else:
        logger.warning("Tidak ada sinyal yang berhasil di-scrape dari semua kategori.")