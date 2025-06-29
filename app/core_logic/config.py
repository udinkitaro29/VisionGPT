# app/core_logic/config.py
import os
from dotenv import load_dotenv

# Memuat variabel dari file .env di root proyek
load_dotenv()

# Token untuk Bot Telegram Anda
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# API Key untuk OpenAI (ChatGPT)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- TAMBAHKAN BARIS INI UNTUK MEMBACA URL DARI .env ---
# URL dasar untuk iframe Autochartist yang akan digunakan oleh scraper dan dashboard
AUTOCHARTIST_BASE_IFRAME_URL = os.getenv("AUTOCHARTIST_BASE_IFRAME_URL")
# --- AKHIR TAMBAHAN ---

# --- TAMBAHAN BARU UNTUK XENDIT ---
#XENDIT_API_KEY = os.getenv("XENDIT_API_KEY")
#XENDIT_CALLBACK_VERIFICATION_TOKEN = os.getenv("XENDIT_CALLBACK_VERIFICATION_TOKEN")

# --- TAMBAHAN BARU ---
# URL Publik tempat server bisa diakses dari internet
PUBLIC_SERVER_URL = os.getenv("PUBLIC_SERVER_URL")

# --- TAMBAHAN BARU UNTUK KEAMANAN DASHBOARD ---
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD")

# --- TAMBAHKAN VARIABEL IPAYMU ---
IPAYMU_VA = os.getenv("IPAYMU_VA")
IPAYMU_API_KEY = os.getenv("IPAYMU_API_KEY")

# --- KONFIGURASI DB BARU ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")