# app/api/routers/signal_router.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas import SignalCreate
from app.services.signal_processor_service import process_and_notify_signal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/signals",
    tags=["Signals"]
)

@router.post("/process-new-signal", status_code=202)
async def process_newly_scraped_signal(signal_input: SignalCreate, background_tasks: BackgroundTasks):
    """
    Endpoint INTERNAL yang dipanggil oleh scraper setelah menemukan sinyal baru.
    Memicu pemrosesan dan pengiriman notifikasi di background.
    """
    logger.info(f"Endpoint /process-new-signal menerima sinyal: {signal_input.pair}")
    
    # Menjalankan proses pengiriman notifikasi di background 
    # agar scraper bisa langsung mendapat respons 202 Accepted.
    background_tasks.add_task(process_and_notify_signal, signal_input)
    
    return {"message": "Sinyal diterima dan dijadwalkan untuk diproses dan dikirim ke pelanggan."}