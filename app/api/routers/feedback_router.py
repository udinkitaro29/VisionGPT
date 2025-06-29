# app/api/routers/feedback_router.py
import logging
from fastapi import APIRouter, Depends, Request
from app.api.schemas import TradeFeedback
from telegram.ext import Application
from app.utils.text_utils import escape_md

router = APIRouter()
logger = logging.getLogger(__name__)

# Fungsi helper untuk mendapatkan aplikasi Telegram dari state FastAPI
def get_telegram_app(request: Request) -> Application:
    # Pastikan app.state.telegram_app sudah di-set di main.py
    return request.app.state.telegram_app

@router.post("/trade-feedback")
async def handle_trade_feedback(
    feedback: TradeFeedback,
    telegram_app: Application = Depends(get_telegram_app)
):
    """Menerima laporan hasil trading dari klien dan mengirim notifikasi ke user."""
    logger.info(f"Menerima feedback trading dari user {feedback.telegram_id}: {feedback.status}")
    
    user_id = feedback.telegram_id
    
    # --- PERBAIKAN: Escape semua variabel sebelum membuat pesan ---
    symbol_md = escape_md(feedback.symbol)
    order_type_md = escape_md(feedback.order_type.upper())
    
    if feedback.status.upper() == 'SUCCESS':
        ticket_md = escape_md(str(feedback.ticket_id))
        message = (
            f"✅ *Eksekusi Berhasil*\n\n"
            f"Order *{order_type_md}* untuk *{symbol_md}* telah berhasil ditempatkan\\.\n"
            f"Nomor Tiket: `{ticket_md}`"
        )
    else:
        comment_md = escape_md(feedback.comment or "Tidak ada detail")
        message = (
            f"❌ *Eksekusi Gagal*\n\n"
            f"Order *{order_type_md}* untuk *{symbol_md}* gagal dieksekusi\\.\n"
            f"Pesan dari Broker: _{comment_md}_"
        )
    # --- AKHIR PERBAIKAN ---
        
    try:
        if telegram_app:
            await telegram_app.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="MarkdownV2"
            )
        else:
            logger.error("Objek aplikasi Telegram tidak ditemukan, tidak bisa mengirim feedback.")
    except Exception as e:
        logger.error(f"Gagal mengirim notifikasi feedback ke user {user_id}: {e}")
        
    return {"status": "feedback received"}