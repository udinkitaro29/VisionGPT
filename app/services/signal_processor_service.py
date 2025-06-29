# app/services/signal_processor_service.py
import logging
import asyncio
from app.api.schemas import SignalCreate
from app.bot.bot_utils import send_signal_notification
from app.utils.text_utils import format_signal_message
from app.database.database import SessionLocal
from app.services import database_service, trading_service
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

logger = logging.getLogger(__name__)

async def process_and_notify_signal(signal_input: SignalCreate):
    """
    Memproses sinyal: mencari pelanggan yang cocok, mengirim notifikasi, 
    dan memicu auto-trade atau menambahkan tombol trading manual.
    """
    pair_to_check = signal_input.pair
    if not pair_to_check:
        logger.warning("Sinyal yang diproses tidak memiliki 'pair'.")
        return

    logger.info(f"Memproses sinyal untuk {pair_to_check} untuk Notifikasi Otomatis...")
    db = SessionLocal()
    try:
        eligible_users = database_service.get_subscribed_users_for_pair(db, pair=pair_to_check)
        if not eligible_users:
            logger.info(f"Tidak ada pelanggan yang cocok untuk menerima sinyal {pair_to_check}.")
            return
        
        signal_dict = signal_input.model_dump()
        message_to_send = format_signal_message(signal_dict)

        # Ambil objek sinyal dari DB untuk mendapatkan ID-nya
        db_signal = db.query(database_service.SignalModel).filter(
            database_service.SignalModel.unique_id == database_service.generate_signal_unique_id(signal_dict)
        ).first()

        if not db_signal:
            logger.error(f"Sinyal dengan unique_id yang sesuai tidak ditemukan di DB untuk pembuatan tombol.")
            return

        # Tentukan arah (direction) untuk logika trading
        entry, tp = signal_dict.get("entry_price"), signal_dict.get("take_profit")
        if entry is not None and tp is not None:
            signal_dict["direction"] = "BUY" if tp > entry else "SELL"
        
        logger.info(f"Mengirim notifikasi sinyal {pair_to_check} ke {len(eligible_users)} pelanggan...")
        for user in eligible_users:
            has_ea_package = user.ea_subscription_status == "ACTIVE" and (user.ea_subscription_end_date is None or user.ea_subscription_end_date > datetime.now())
            
            # --- LOGIKA AUTO-TRADING ---
            if user.auto_trade_enabled and has_ea_package:
                logger.info(f"User {user.telegram_id} mengaktifkan auto-trade. Memicu trading_service...")
                await trading_service.send_trade_command_to_client(user.telegram_id, signal_dict, "MARKET")
            
            # --- KIRIM NOTIFIKASI DENGAN TOMBOL JIKA PUNYA PAKET EA ---
            reply_markup = None
            if has_ea_package:
                keyboard = [[InlineKeyboardButton("👆 Trading Manual", callback_data=f"manual_trade_start_{db_signal.id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

            await send_signal_notification(str(user.telegram_id), message_to_send, reply_markup)
            await asyncio.sleep(0.5)
    finally:
        db.close()