# app/api/main.py
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.database_service import get_pending_invoices # Tambahkan get_pending_invoices
from app.bot.bot_utils import send_signal_notification # Gunakan ini untuk kirim pengingat
# --- PERBAIKAN IMPORT ---
from app.services.database_service import get_pending_invoices
from app.database.database import SessionLocal # Impor SessionLocal dari lokasi yang benar
# --- AKHIR PERBAIKAN ---

# Import semua komponen yang dibutuhkan dari modul lain
from app.bot.core import setup_bot_application, start_bot_task, stop_telegram_bot_polling
# --- PERBAIKAN: Ganti webhook_router dengan ipaymu_router ---
from app.api.routers import (
    signal_router, 
    dashboard_router, 
    websocket_router, 
    feedback_router,
    ipaymu_router  # Impor router baru untuk iPaymu
)
# --- AKHIR PERBAIKAN ---
# from app.database.database import create_db_and_tables # Tidak dipakai lagi, gunakan Alembic

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot_task = None 

scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

# --- FUNGSI BARU UNTUK TUGAS PENGINGAT ---
async def send_payment_reminders():
    logger.info("Scheduler: Menjalankan tugas pengecekan pembayaran pending...")
    db = SessionLocal()
    try:
        # Kita perlu buat fungsi get_pending_invoices di database_service
        pending_invoices = database_service.get_pending_invoices(db)
        if not pending_invoices:
            logger.info("Tidak ada pembayaran pending yang perlu diingatkan.")
            return

        for invoice in pending_invoices:
            # Kirim pengingat jika invoice dibuat lebih dari 1 jam yang lalu
            time_since_creation = datetime.now(invoice.created_at.tzinfo) - invoice.created_at
            if time_since_creation > timedelta(hours=1):
                logger.info(f"Mengirim pengingat pembayaran ke user {invoice.user_telegram_id}")
                message = (
                    f"👋 Halo! Kami melihat Anda belum menyelesaikan pembayaran untuk paket langganan Anda.\n\n"
                    f"Segera selesaikan melalui link berikut:\n{invoice.payment_url}"
                )
                await send_signal_notification(str(invoice.user_telegram_id), message)
                # Hapus invoice atau tandai sudah diingatkan agar tidak dikirim terus
                # (logika ini bisa disempurnakan nanti)
    finally:
        db.close()
# --- AKHIR FUNGSI ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Mengelola startup dan shutdown untuk Bot Telegram dan Database."""
    global bot_task
    logger.info("### Memulai Aplikasi (API & Bot)... ###")
    
    logger.info("Database siap (manajemen tabel oleh Alembic).")

    # Setup Bot Telegram dan simpan ke state FastAPI
    telegram_app = setup_bot_application()
    app.state.telegram_app = telegram_app
    bot_task = start_bot_task()
    logger.info("Bot Telegram siap dan polling dimulai di background.")
    # --- TAMBAHAN: JALANKAN SCHEDULER ---
    try:
        # Jalankan setiap jam
        scheduler.add_job(send_payment_reminders, 'interval', hours=1, id="payment_reminder_job")
        scheduler.start()
        logger.info("Scheduler untuk pengingat pembayaran dimulai.")
    except Exception as e:
        logger.error(f"Gagal memulai scheduler pengingat: {e}")
    # --- AKHIR TAMBAHAN ---
    yield # Aplikasi sekarang berjalan

    # --- SHUTDOWN SEQUENCE ---
    logger.info("### Memulai Proses Shutdown... ###")
    await stop_telegram_bot_polling()
    # ... (sisa logika shutdown)

app = FastAPI(
    title="Trading Signal Bot API",
    description="API untuk scraping, notifikasi, dashboard, dan koneksi trading.",
    version="1.3.0", # Naikkan versi karena migrasi payment gateway
    lifespan=lifespan
)

# --- Daftarkan semua router ---
app.include_router(signal_router.router)
app.include_router(dashboard_router.router)
app.include_router(websocket_router.router)
app.include_router(feedback_router.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(ipaymu_router.router, prefix="/webhooks", tags=["Webhooks"]) # <<< Gunakan router iPaymu

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html><head><title>Trading Signal Bot</title><meta http-equiv="refresh" content="0; url='/dashboard/'" /></head>
    <body><p>Loading dashboard...</p></body>
    </html>
    """

@app.get("/status", tags=["Utilities"])
async def get_status():
    return { "status": "OK", "bot_polling_running": bot_task is not None and not bot_task.done() }