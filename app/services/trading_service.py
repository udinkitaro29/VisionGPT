# app/services/trading_service.py
import logging
from typing import Dict
from app.utils.connection_manager import manager
from app.database.database import SessionLocal
from app.services import database_service
from datetime import datetime

logger = logging.getLogger(__name__)

async def send_trade_command_to_client(user_id: int, signal_data: dict, order_type: str):
    """
    Menggabungkan simbol, membersihkan data, dan mengirimkannya via WebSocket.
    """
    db = SessionLocal()
    try:
        user = database_service.get_user_by_telegram_id(db, user_id)
        if not user:
            logger.error(f"User {user_id} tidak ditemukan untuk pengiriman perintah trade.")
            return

        base_symbol = signal_data.get('pair', '')
        prefix = user.symbol_prefix or ""
        suffix = user.symbol_suffix or ""
        final_symbol = f"{prefix}{base_symbol}{suffix}"
        
        # --- PERUBAHAN DI SINI ---
        # Buat salinan data dan hapus field yang tidak perlu
        data_to_send = signal_data.copy()
        data_to_send['pair'] = final_symbol
        data_to_send.pop('image_url', None) # Hapus image_url
        data_to_send.pop('short_description', None) # Hapus deskripsi panjang juga
        
        # Sanitasi objek datetime menjadi string
        for key, value in data_to_send.items():
            if isinstance(value, datetime):
                data_to_send[key] = value.isoformat()
        # --- AKHIR PERUBAHAN ---

        logger.info(f"Mengirim perintah untuk simbol final: {final_symbol}")
        
        command_payload = {
            "action": "EXECUTE_TRADE",
            "order_type": order_type.upper(),
            "signal": data_to_send # Gunakan data yang sudah bersih
        }
        await manager.send_trade_command(user_id, command_payload)
    finally:
        db.close()