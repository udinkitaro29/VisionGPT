# test_mt5_connection.py
import MetaTrader5 as mt5
from datetime import datetime
import time

print("Memulai script tes koneksi MT5...")

try:
    import MetaTrader5 as mt5
except ImportError:
    print("Library 'MetaTrader5' tidak ditemukan. Instal dengan: pip install MetaTrader5")
    exit()

if not mt5.initialize():
    print(f"Gagal menginisialisasi MT5, error code = {mt5.last_error()}")
    print("\n--- PANDUAN PEMECAHAN MASALAH ---")
    print("1. PASTIKAN: Aplikasi terminal MetaTrader 5 (desktop) sedang berjalan.")
    print("2. PASTIKAN: Anda sudah login ke akun trading di terminal tersebut.")
    print("3. PASTIKAN: Opsi 'Tools -> Options -> Expert Advisors -> Allow Algo Trading' sudah dicentang.")
    mt5.shutdown()
    exit()

print(f"Koneksi ke Terminal MT5 berhasil. Versi Terminal: {mt5.version()}")

account_info = mt5.account_info()
if account_info:
    account_info_dict = account_info._asdict()
    print("\n--- Informasi Akun ---")
    print(f"Login     : {account_info_dict['login']}")
    print(f"Nama      : {account_info_dict['name']}")
    print(f"Broker    : {account_info_dict['server']}")
    print(f"Balance   : {account_info_dict['balance']} {account_info_dict['currency']}")
    print("--------------------")
else:
    print(f"Gagal mengambil informasi akun, error code = {mt5.last_error()}")

symbol = "EURUSD"
print(f"\nMencoba mengambil harga tick terakhir untuk {symbol}...")

symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Simbol {symbol} tidak ditemukan.")
else:
    if not symbol_info.visible:
        print(f"Simbol {symbol} tidak terlihat, mencoba mengaktifkannya...")
        if not mt5.symbol_select(symbol, True):
            print(f"Gagal mengaktifkan {symbol}.")
        else:
            time.sleep(1)

    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print("\n--- Harga Tick Terakhir ---")
        # --- PERBAIKAN DI SINI ---
        print(f"Simbol    : {symbol}") # Kita sudah tahu simbolnya dari variabel 'symbol'
        # --- AKHIR PERBAIKAN ---
        print(f"Waktu     : {datetime.fromtimestamp(tick.time)}")
        print(f"Harga Bid : {tick.bid}")
        print(f"Harga Ask : {tick.ask}")
        print("-------------------------")
    else:
        print(f"Gagal mengambil harga tick untuk {symbol}, error code = {mt5.last_error()}")

print("\nMenutup koneksi ke MT5...")
mt5.shutdown()
print("Koneksi ditutup. Tes selesai.")