# app/bot/core.py
import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from app.bot.handlers import start_command, menu_command, button_handler, help_command, settings_command, message_handler
from app.core_logic.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

telegram_app: Application = None
telegram_app_task = None

def setup_bot_application() -> Application:
    """Buat dan konfigurasi instance Aplikasi Telegram."""
    global telegram_app
    logger.info("Menginisialisasi aplikasi Telegram Bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Daftarkan semua command handler
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command)) # <<< TAMBAHKAN HANDLER INI
    application.add_handler(CommandHandler("settings", settings_command))

    # Daftarkan handler untuk semua penekanan tombol inline
    application.add_handler(CallbackQueryHandler(button_handler))
     # Tambahkan message handler untuk menangkap input teks dari pengguna
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    telegram_app = application
    logger.info("Aplikasi Telegram Bot berhasil diinisialisasi.")
    return application

# ... (fungsi run_telegram_bot_polling, stop_telegram_bot_polling, start_bot_task tetap sama persis) ...
async def run_telegram_bot_polling():
    if not telegram_app: return logger.error("Aplikasi Telegram belum di-setup.")
    logger.info("Memulai polling Telegram Bot...")
    try:
        await telegram_app.initialize()
        await telegram_app.updater.start_polling()
        await telegram_app.start()
        logger.info("Telegram Bot polling telah dimulai dan aplikasi berjalan.")
        while telegram_app.updater and telegram_app.updater.running: await asyncio.sleep(1)
    except Exception as e: logger.error(f"Error saat menjalankan polling Telegram Bot: {e}", exc_info=True)
    finally:
        if telegram_app and telegram_app.updater and telegram_app.updater.running: await telegram_app.updater.stop()
        if telegram_app and telegram_app.running: await telegram_app.stop()
        logger.info("Telegram Bot polling telah dihentikan sepenuhnya.")

async def stop_telegram_bot_polling():
    global telegram_app_task
    if telegram_app and telegram_app.updater and telegram_app.updater.running: await telegram_app.updater.stop()
    if telegram_app and telegram_app.running: await telegram_app.stop()
    if telegram_app_task and not telegram_app_task.done():
        telegram_app_task.cancel()
        try: await telegram_app_task
        except asyncio.CancelledError: logger.info("Task polling Telegram Bot berhasil dibatalkan.")
    logger.info("Proses shutdown bot selesai.")


def start_bot_task():
    global telegram_app_task
    if not telegram_app: return None
    loop = asyncio.get_event_loop()
    telegram_app_task = loop.create_task(run_telegram_bot_polling())
    return telegram_app_task

# FUNGSI send_signal_notification SUDAH DIHAPUS DARI SINI