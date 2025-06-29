# test_ipaymu_signature.py
import json
import hashlib
import hmac
from datetime import datetime

# --- MASUKKAN KREDENSIAL SANDBOX ANDA DI SINI ---
# Salin-tempel lagi dengan sangat hati-hati dari dashboard iPaymu Sandbox
VA = "0000002143628106"
API_KEY = "SANDBOX997B2CE5-8AD7-4349-ADD7-373045F28BA0"
# --------------------------------------------------

# Contoh body request, sama seperti yang kita gunakan
body = {
    "product": ["Paket Tes"],
    "qty": [1],
    "price": [10000],
    "returnUrl": "https://t.me/NAMA_BOT_ANDA",
    "notifyUrl": "https://webhook.site/test", # Gunakan URL dummy untuk tes ini
    "referenceId": "test-12345",
}

# --- PROSES PEMBUATAN SIGNATURE (Sesuai Logika Terakhir Kita) ---
body_json = json.dumps(body, separators=(',', ':'))
hashed_body_lower = hashlib.sha256(body_json.encode()).hexdigest().lower()
timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
string_to_sign = f"POST:{VA}:{timestamp}:{hashed_body_lower}"
signature = hmac.new(API_KEY.encode(), string_to_sign.encode(), hashlib.sha256).hexdigest()


# --- CETAK SEMUA KOMPONEN UNTUK POSTMAN ---
print("==================================================================")
print("=== GUNAKAN DATA DI BAWAH INI UNTUK TES DI POSTMAN ===")
print("==================================================================")
print("\nMETHOD: POST")
print(f"URL: https://sandbox.ipaymu.com/api/v2/payment")
print("\nHEADERS:")
print(f"va: {VA}")
print(f"signature: {signature}")
print(f"timestamp: {timestamp}")
print(f"Content-Type: application/json")
print("\nBODY (pilih mode 'raw' dan 'JSON' di Postman):")
print(body_json)
print("\n==================================================================")