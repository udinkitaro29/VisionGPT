# app/services/xendit_service.py
import logging
import xendit
from datetime import datetime
from app.core_logic.config import XENDIT_API_KEY
from app.core_logic.packages import PACKAGES

logger = logging.getLogger(__name__)

if not XENDIT_API_KEY:
    logger.warning("XENDIT_API_KEY tidak ditemukan. Fungsi pembayaran tidak akan bekerja.")
else:
    xendit.api_key = XENDIT_API_KEY

def create_invoice(telegram_id: int, package_key: str):
    """
    Membuat invoice di Xendit untuk paket tertentu.
    """
    if not XENDIT_API_KEY:
        logger.error("Tidak bisa membuat invoice, XENDIT_API_KEY tidak diatur.")
        return None

    package_details = PACKAGES.get(package_key)
    if not package_details:
        logger.error(f"Paket dengan key '{package_key}' tidak ditemukan.")
        return None
    
    timestamp = int(datetime.now().timestamp())
    external_id = f"user-{telegram_id}-package-{package_key}-{timestamp}"

    try:
        # Panggil API Xendit untuk membuat invoice
        invoice = xendit.Invoice.create(
            external_id=external_id,
            amount=package_details["price"],
            # --- PERBAIKAN: TAMBAHKAN payer_email ---
            # Kita buat email unik dummy berdasarkan ID Telegram pengguna
            payer_email=f"user-{telegram_id}@yourbot.com", 
            # --- AKHIR PERBAIKAN ---
            description=f"Langganan {package_details['name']} untuk Telegram User ID {telegram_id}",
            invoice_duration=3600,
            currency="IDR",
            success_redirect_url="https://t.me/VisionGPTv2_bot", # GANTI NAMA_BOT_ANDA
            failure_redirect_url="https://t.me/VisionGPTv2_bot"
        )
        logger.info(f"Invoice berhasil dibuat untuk {external_id} dengan URL: {invoice.invoice_url}")
        return invoice.invoice_url
        
    except Exception as e:
        logger.error(f"Gagal membuat invoice di Xendit: {e}", exc_info=True)
        return None