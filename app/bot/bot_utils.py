# app/bot/bot_utils.py
import logging
import re
from typing import Optional
from telegram import constants, InlineKeyboardMarkup
from app.bot import core as bot_core

logger = logging.getLogger(__name__)

def escape_md(text: Optional[str]) -> str:
    """Meng-escape karakter khusus untuk Telegram MarkdownV2."""
    if text is None:
        return "N/A"
    text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}!'
    translator = str.maketrans({char: f"\\{char}" for char in escape_chars})
    return text.translate(translator)

async def send_signal_notification(
    chat_id: str, 
    message: str, 
    reply_markup: Optional[InlineKeyboardMarkup] = None
):
    """
    Mengirim pesan notifikasi yang sudah diformat ke chat ID tertentu.
    Sekarang bisa menerima tombol inline (reply_markup).
    """
    if not bot_core.telegram_app:
        logger.error("Bot belum diinisialisasi, tidak bisa mengirim pesan.")
        return

    try:
        await bot_core.telegram_app.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=constants.ParseMode.MARKDOWN_V2,
            reply_markup=reply_markup # <<< Gunakan parameter reply_markup di sini
        )
        logger.info(f"Notifikasi berhasil dikirim ke chat_id {chat_id}")
    except Exception as e:
        logger.error(f"Gagal mengirim notifikasi ke {chat_id}: {e}", exc_info=True)
        if "Can't parse entities" in str(e):
            logger.warning("Gagal mengirim pesan karena format Markdown. Mencoba mengirim sebagai teks biasa...")
            try:
                # Hapus karakter Markdown sebelum mengirim ulang
                plain_text = re.sub(r'([_*\[\]()~`>#+-=|{}.!])', '', message)
                await bot_core.telegram_app.bot.send_message(chat_id=chat_id, text=plain_text, reply_markup=reply_markup)
                logger.info(f"Notifikasi teks biasa (fallback) berhasil dikirim ke {chat_id}")
            except Exception as e_fallback:
                logger.error(f"Gagal mengirim notifikasi teks biasa (fallback) ke {chat_id}: {e_fallback}", exc_info=True)