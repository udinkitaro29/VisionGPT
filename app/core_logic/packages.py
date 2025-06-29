# app/core_logic/packages.py

# Daftar aset untuk setiap kategori paket
# Anda bisa menyesuaikan dan menambahkan isinya sesuai kebutuhan
# --- KAMUS PEMETAAN SIMBOL ---
# Kunci (Key) adalah nama dari Autochartist (dalam huruf besar)
# Nilai (Value) adalah nama simbol yang digunakan di MT5 Anda
SYMBOL_MAP = {
    "GOLD SPOT": "XAUUSD",
    "US 500": "US500", # Atau nama lain di MT5 Anda
    "BRENT CRUDE": "UKOIL", # Contoh, sesuaikan dengan MT5 Anda
    "US CRUDE OIL": "USOIL", # Contoh, sesuaikan dengan MT5 Anda
    "BTCUSD": "BTCUSD", # Jika sama, tetap definisikan
    "ETHUSD": "ETHUSD",
    # Tambahkan semua pemetaan lain yang Anda butuhkan di sini
}
# --- AKHIR KAMUS ---
PACKAGE_ASSETS = {
    "GOLD": ["XAUUSD"], # <<< Gunakan XAUUSD, bukan GOLD SPOT
    "FOREX": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", # Major
        "GBPJPY", "EURJPY", "AUDJPY", "CADJPY", "CHFJPY", # JPY Crosses
        "EURGBP", "EURAUD", "EURCAD", "EURCHF", "EURNZD", # EUR Crosses
        "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", # GBP Crosses
    ],
    "CRYPTO": ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD"], # Contoh
}
# Paket 'ALL' akan mencakup semua aset di atas.
# Paket gabungan (misal Gold + Forex) akan kita tangani dengan logika.

# Definisi detail paket
PACKAGES = {
    # Paket Utama
    "gold_monthly": {
        "name": "GOLD (Bulanan)", "price": 149000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["GOLD"], "type": "main"
    },
    "forex_monthly": {
        "name": "FOREX (Bulanan)", "price": 175000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["FOREX"], "type": "main"
    },
    "crypto_monthly": {
        "name": "CRYPTO (Bulanan)", "price": 99000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["CRYPTO"], "type": "main"
    },
    "all_monthly": {
        "name": "ALL IN (Bulanan)", "price": 259000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["GOLD"] + PACKAGE_ASSETS["FOREX"] + PACKAGE_ASSETS["CRYPTO"], "type": "main"
    },
        "all_monthly": {
        "name": "ALL IN (Bulanan)", "price": 259000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["GOLD"] + PACKAGE_ASSETS["FOREX"] + PACKAGE_ASSETS["CRYPTO"], "type": "main"
    },
        "all_yearly": {
        "name": "ALL IN (Tahunan)", "price": 1990000, "duration_days": 365,
        "assets": PACKAGE_ASSETS["GOLD"] + PACKAGE_ASSETS["FOREX"] + PACKAGE_ASSETS["CRYPTO"], "type": "main"
    },    
    # Paket Gabungan
    "gold_forex_monthly": {
        "name": "GOLD + FOREX (Bulanan)", "price": 249000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["GOLD"] + PACKAGE_ASSETS["FOREX"], "type": "main"
    },
    "gold_crypto_monthly": {
        "name": "GOLD + CRYPTO (Bulanan)", "price": 239000, "duration_days": 30,
        "assets": PACKAGE_ASSETS["GOLD"] + PACKAGE_ASSETS["CRYPTO"], "type": "main"
    },
    # Paket Add-on
    "pro_ea_monthly": {
        "name": "PRO EA (Add-on Bulanan)", "price": 199000, "duration_days": 30,
        "description": "Mengaktifkan fitur Trading Manual & Otomatis.", "type": "addon"
    },
    # Paket Trial
    "trial_paid": {
        "name": "TRIAL GOLD (7 Hari)", "price": 49000, "duration_days": 7,
        "assets": PACKAGE_ASSETS["GOLD"], "type": "trial"
    }
    
}