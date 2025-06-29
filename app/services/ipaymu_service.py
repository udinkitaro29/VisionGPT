# app/services/ipaymu_service.py
import logging
import requests
import json
import hashlib
import hmac
from datetime import datetime
from app.core_logic.config import IPAYMU_VA, IPAYMU_API_KEY, PUBLIC_SERVER_URL
from app.core_logic.packages import PACKAGES
from app.services import database_service # Pastikan ini diimpor
from app.database.database import SessionLocal # Pastikan ini diimpor

logger = logging.getLogger(__name__)

# --- PERUBAHAN UTAMA: Ganti URL ke mode LIVE ---
IPAYMU_API_URL = "https://my.ipaymu.com//api/v2/payment"
# --- AKHIR PERUBAHAN ---

def create_payment_link(telegram_id: int, package_key: str):
    """Membuat payment link di iPaymu sesuai dengan contoh kode resmi."""
    if not IPAYMU_VA or not IPAYMU_API_KEY:
        logger.error("Kredensial iPaymu (VA atau API Key) di file .env belum diatur.")
        return None

    package_details = PACKAGES.get(package_key)
    if not package_details:
        logger.error(f"Paket dengan key '{package_key}' tidak ditemukan.")
        return None
        
    reference_id = f"user-{telegram_id}-package-{package_key}-{int(datetime.now().timestamp())}"

    # --- PERBAIKAN FINAL PADA STRUKTUR BODY ---
    # Sesuaikan 100% dengan contoh resmi redirect-payment.py
    body = {
        "product": [package_details["name"]], # <<< Gunakan 'product' dan harus berupa list
        "qty": [1],                          # <<< Harus berupa list
        "price": [package_details["price"]], # <<< Harus berupa list
        "returnUrl": f"https://t.me/NAMA_BOT_ANDA", # Ganti dengan username bot Anda
        "notifyUrl": f"https://{PUBLIC_SERVER_URL}/webhooks/ipaymu",
        "referenceId": reference_id,
    }
    # --- AKHIR PERBAIKAN ---
    
    body_json = json.dumps(body, separators=(',', ':'))
    
    # --- PEMBUATAN SIGNATURE YANG BENAR SESUAI CONTOH GITHUB ---
    
    # 1. Buat hash SHA256 dari body JSON
    hashed_body = hashlib.sha256(body_json.encode()).hexdigest()

    # 2. Susun StringToSign sesuai contoh: POST:VA:HASH(BODY):APIKEY
    # Timestamp tidak digunakan di sini, tetapi tetap dikirim di header.
    string_to_sign = f"POST:{IPAYMU_VA}:{hashed_body}:{IPAYMU_API_KEY}"

    # 3. Generate signature HMAC-SHA256 dan ubah ke lowercase
    signature = hmac.new(IPAYMU_API_KEY.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest().lower()

    # --- AKHIR PERBAIKAN ---

    headers = {
        'Content-Type': 'application/json',
        'va': IPAYMU_VA,
        'signature': signature,
        'timestamp': datetime.now().strftime('%Y%m%d%H%M%S') # Timestamp tetap dikirim di header
    }

    logger.info("Mengirim final request ke iPaymu...")
    logger.debug(f"BODY FINAL: {body_json}")
    logger.debug(f"StringToSign: {string_to_sign}")
    logger.debug(f"Signature: {signature}")

    try:
        response = requests.post(IPAYMU_API_URL, headers=headers, data=body_json, timeout=15)
        response_data = response.json()

        if response.status_code == 200 and response_data.get("Status") == 200:
            payment_url = response_data["Data"]["Url"]
            logger.info(f"Payment link iPaymu BERHASIL dibuat untuk {reference_id}")
                        # --- TAMBAHAN: CATAT INVOICE KE DB ---
            db = SessionLocal()
            try:
                database_service.create_payment_invoice(
                    db, user_id=telegram_id, ref_id=reference_id, 
                    url=payment_url, pkg_key=package_key
                )
            finally:
                db.close()
            # --- AKHIR TAMBAHAN ---
            return payment_url
        else:
            logger.error(f"iPaymu API error: {response_data.get('Message')} (Status: {response_data.get('Status')}) | Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Gagal menghubungi API iPaymu: {e}", exc_info=True)
        return None