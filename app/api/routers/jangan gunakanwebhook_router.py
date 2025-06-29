# app/api/routers/webhook_router.py
import logging
import re
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks
from app.core_logic.config import XENDIT_CALLBACK_VERIFICATION_TOKEN
from app.core_logic.packages import PACKAGES
from app.database.database import SessionLocal
from app.services import database_service
from app.bot import core as bot_core
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)

def escape_md(text: Optional[str]) -> str:
    """Meng-escape karakter khusus untuk Telegram MarkdownV2."""
    if text is None:
        return ""
    text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    translator = str.maketrans({char: f"\\{char}" for char in escape_chars})
    return text.translate(translator)

async def perform_background_update_and_notify(payload: dict):
    """
    Fungsi background task yang melakukan update DB dan mengirim notifikasi.
    Versi ini sudah diperbaiki untuk menangani tipe paket dan nama kolom DB yang benar.
    """
    logger.info("--- Background task 'perform_background_update_and_notify' DIMULAI ---")
    db = SessionLocal()
    try:
        external_id = payload.get("external_id")
        if not external_id:
            logger.error("Background task: external_id tidak ditemukan di payload.")
            return

        logger.info(f"Background task: Memproses external_id: {external_id}")
        match = re.search(r"user-(\d+)-package-([a-zA-Z0-9_]+)-", external_id)
        if not match:
            logger.error(f"Background task: Format external_id '{external_id}' tidak sesuai.")
            return

        telegram_id = int(match.group(1))
        package_key = match.group(2)
        package_details = PACKAGES.get(package_key)

        if not package_details:
            logger.error(f"Background task: Package key '{package_key}' dari external_id tidak ditemukan.")
            return
            
        logger.info(f"Background task: Memanggil DB service untuk update user {telegram_id}...")
        # --- PERBAIKAN: Kirim 'package_type' ke service ---
        updated_user = database_service.update_user_subscription(
            db=db,
            telegram_id=telegram_id,
            package_name=package_details["name"],
            duration_days=package_details["duration_days"],
            package_type=package_details.get("type", "main") # Mengambil tipe paket
        )
        # --- AKHIR PERBAIKAN ---
        
        if updated_user and bot_core.telegram_app:
            logger.info(f"Background task: User {telegram_id} berhasil diupdate di DB. Menyiapkan pesan konfirmasi...")
            
            # Tentukan paket mana yang akan ditampilkan di notifikasi konfirmasi
            package_name_to_display = ""
            end_date_to_display = None
            
            package_type = package_details.get("type", "main")
            if package_type == 'addon':
                package_name_to_display = package_details.get("name", "Add-on")
                end_date_to_display = updated_user.ea_subscription_end_date
            else: # Untuk 'main' atau 'trial'
                package_name_to_display = updated_user.main_package_name
                end_date_to_display = updated_user.main_subscription_end_date

            package_name_escaped = escape_md(package_name_to_display)
            end_date_escaped = escape_md(end_date_to_display.strftime('%d %B %Y')) if end_date_to_display else "N/A"
            
            confirmation_message = (
                f"✅ *Pembayaran Berhasil\\!*\n\n"
                f"Terima kasih, langganan Anda untuk paket *{package_name_escaped}* "
                f"kini aktif hingga *{end_date_escaped}*\\."
            )

            try:
                logger.info(f"Background task: Mencoba mengirim pesan konfirmasi ke {telegram_id}...")
                await bot_core.telegram_app.bot.send_message(
                    chat_id=telegram_id, 
                    text=confirmation_message,
                    parse_mode="MarkdownV2"
                )
                logger.info(f"Background task: Pesan konfirmasi BERHASIL dikirim ke {telegram_id}.")
            except Exception as e_telegram:
                logger.error(f"Background task: GAGAL mengirim pesan telegram. Error: {e_telegram}", exc_info=True)
        else:
            logger.error(f"Background task: Gagal mengupdate user atau objek telegram_app adalah None.")
            
    except Exception as e_bg:
        logger.error(f"Background task: Terjadi error tidak terduga. Error: {e_bg}", exc_info=True)
    finally:
        db.close()
        logger.info("--- Background task 'perform_background_update_and_notify' SELESAI ---")


@router.post("/xendit")
async def xendit_invoice_webhook(request: Request, background_tasks: BackgroundTasks, x_callback_token: str = Header(None)):
    """Endpoint untuk menerima callback/webhook dari Xendit setelah invoice dibayar."""
    logger.info("Menerima request webhook dari Xendit...")
    if x_callback_token != XENDIT_CALLBACK_VERIFICATION_TOKEN:
        logger.error("Token verifikasi webhook Xendit tidak valid!")
        raise HTTPException(status_code=401, detail="Invalid verification token")
    try:
        payload = await request.json()
        logger.info(f"Payload webhook Xendit diterima: {payload}")
    except Exception as e:
        logger.error(f"Gagal mem-parsing JSON dari webhook Xendit: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    if payload.get("status") == "PAID":
        logger.info(f"Invoice {payload.get('external_id')} telah dibayar (PAID). Menambahkan tugas ke background...")
        background_tasks.add_task(perform_background_update_and_notify, payload)
    else:
        logger.info(f"Menerima status webhook '{payload.get('status')}', bukan 'PAID'. Diabaikan.")
    logger.info("Merespons 200 OK ke Xendit seketika.")
    return {"status": "success"}