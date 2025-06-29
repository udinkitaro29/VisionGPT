# app/utils/connection_manager.py
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Dictionary untuk menyimpan koneksi aktif: {telegram_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"Klien eksekutor untuk user {user_id} terhubung.")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"Klien eksekutor untuk user {user_id} terputus.")

    async def send_trade_command(self, user_id: int, command: dict):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(command)
                logger.info(f"Perintah trading berhasil dikirim ke user {user_id} via WebSocket.")
            except Exception as e:
                logger.error(f"Gagal mengirim perintah ke user {user_id} via WebSocket: {e}")
                self.disconnect(user_id) # Putuskan koneksi jika error
        else:
            logger.warning(f"Tidak ada koneksi WebSocket aktif untuk user {user_id}. Perintah tidak terkirim.")

# Buat satu instance global dari manajer ini untuk digunakan di seluruh aplikasi
manager = ConnectionManager()