# app/api/routers/ipaymu_router.py
import logging
import re
from fastapi import APIRouter, Request, Depends, HTTPException
from app.services import database_service
from app.core_logic.packages import PACKAGES
from telegram.ext import Application
from app.utils.text_utils import escape_md
from datetime import datetime # <<< TAMBAHKAN IMPORT INI

# --- PERBAIKAN IMPORT ---
from app.database.database import SessionLocal
# --- AKHIR PERBAIKAN ---

router = APIRouter()
logger = logging.getLogger(__name__)

def get_telegram_app(request: Request) -> Application:
    return request.app.state.telegram_app

@router.post("/ipaymu")
async def ipaymu_notify_webhook(
    request: Request, 
    telegram_app: Application = Depends(get_telegram_app)
):
    """Endpoint untuk menerima Notifikasi (IPN) dari iPaymu."""
    try:
        payload = await request.form()
        logger.info(f"Menerima notifikasi iPaymu: {payload}")

        status = payload.get("status")
        reference_id = payload.get("reference_id")

        if status == "berhasil" and reference_id:
            logger.info(f"Pembayaran berhasil untuk reference_id: {reference_id}")
            try:
                match = re.search(r"user-(\d+)-package-([a-zA-Z0-9_]+)-", reference_id)
                if not match:
                    logger.error(f"Format reference_id '{reference_id}' tidak sesuai.")
                    return {"status": "error", "message": "Invalid reference_id format"}

                telegram_id = int(match.group(1))
                package_key = match.group(2)
                package_details = PACKAGES.get(package_key)

                if package_details:
                    db = SessionLocal() # <<< Sekarang ini akan bekerja
                    try:
                                # --- TAMBAHAN: UPDATE STATUS INVOICE ---
                        invoice = db.query(database_service.PaymentInvoiceModel).filter_by(reference_id=reference_id).first()
                        if invoice and invoice.status == "PENDING":
                            invoice.status = "PAID"
                            invoice.paid_at = datetime.now()
                            invoice.ipaymu_trx_id = payload.get("trx_id")
                            db.commit()
                            logger.info(f"Status invoice untuk reference_id {reference_id} diupdate menjadi PAID.")
                                    # --- AKHIR TAMBAHAN ---
                        updated_user = database_service.update_user_subscription(
                            db=db,
                            telegram_id=telegram_id,
                            package_name=package_details["name"],
                            duration_days=package_details["duration_days"],
                            package_type=package_details.get("type", "main")
                        )
                        
                        if updated_user and telegram_app:
                            end_date = updated_user.ea_subscription_end_date if package_details.get("type") == "addon" else updated_user.main_subscription_end_date
                            package_name_escaped = escape_md(updated_user.main_package_name or package_details["name"])
                            end_date_escaped = escape_md(end_date.strftime('%d %B %Y'))
                            
                            confirmation_message = (
                                f"✅ *Pembayaran Berhasil\\!*\n\n"
                                f"Terima kasih, langganan Anda untuk paket *{package_name_escaped}* "
                                f"kini aktif hingga *{end_date_escaped}*\\."
                            )
                            await telegram_app.bot.send_message(
                                chat_id=telegram_id, 
                                text=confirmation_message,
                                parse_mode="MarkdownV2"
                            )
                    finally:
                        db.close()
            except Exception as e:
                logger.error(f"Gagal memproses notifikasi iPaymu: {e}", exc_info=True)
        
        return {"status": "callback received"}
    
    except Exception as e:
        logger.error(f"Error tidak terduga saat memproses webhook iPaymu: {e}", exc_info=True)
        return {"status": "error", "message": "Failed to process callback"}