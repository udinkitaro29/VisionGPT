# run_scraper.py
import time
import requests # <<< Gunakan requests untuk mengirim data
import logging
from app.scraper.autochartist_scraper import scrape_all_autochartist_data
from app.database.database import SessionLocal
from app.services import database_service

# Konfigurasi
SCRAPER_INTERVAL_SECONDS = 180 # 15 menit
# Endpoint API di server FastAPI kita untuk memproses sinyal baru
API_PROCESS_SIGNAL_URL = "http://127.0.0.1:8000/api/v1/signals/process-new-signal"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScraperProcess")

def run_scraper_cycle():
    logger.info("=== MEMULAI SIKLUS SCRAPING & SINKRONISASI ===")
    
    active_signals_from_web = scrape_all_autochartist_data()
    logger.info(f"Scraper selesai, mendapatkan {len(active_signals_from_web)} sinyal aktif dari web.")
    
    if not active_signals_from_web:
        logger.warning("Tidak ada sinyal yang ditemukan dari web. Melewati siklus sinkronisasi.")
        return

    db = SessionLocal()
    try:
        active_unique_ids = []
        for signal_data in active_signals_from_web:
            db_signal, is_new = database_service.upsert_signal(db, signal_data=signal_data)
            active_unique_ids.append(db_signal.unique_id)
            
            if is_new:
                logger.info(f"Sinyal BARU ditemukan untuk {signal_data.get('pair')}. Mengirim ke API untuk diproses...")
                try:
                    # Kirim sinyal baru ke endpoint FastAPI
                    # Timeout diatur agar tidak menunggu terlalu lama
                    response = requests.post(API_PROCESS_SIGNAL_URL, json=signal_data, timeout=10)
                    response.raise_for_status() # Akan error jika status code bukan 2xx
                    logger.info(f"Berhasil mengirim sinyal {signal_data.get('pair')} ke API. Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Gagal mengirim sinyal ke API: {e}")
                # Jeda kecil antar request API
                time.sleep(1) 
        
        logger.info("Memulai proses penghapusan sinyal tidak aktif...")
        database_service.delete_inactive_signals(db, active_unique_ids=active_unique_ids)
    finally:
        db.close()
    
    logger.info(f"Siklus sinkronisasi selesai.")


if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Library 'requests' tidak ditemukan. Mohon instal dengan 'pip install requests'")
        exit()
        
    logger.info("Scraper mandiri dimulai.")
    logger.info(f"Scraper akan berjalan setiap {SCRAPER_INTERVAL_SECONDS} detik.")
    while True:
        try:
            run_scraper_cycle()
        except Exception as e:
            logger.error(f"Terjadi error fatal di siklus utama scraper: {e}", exc_info=True)
        logger.info(f"Siklus berikutnya akan dimulai dalam {SCRAPER_INTERVAL_SECONDS} detik...")
        time.sleep(SCRAPER_INTERVAL_SECONDS)