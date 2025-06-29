# app/api/routers/websocket_router.py
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["WebSocket"]
)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Tetap jaga koneksi tetap hidup dengan menunggu pesan (ping/pong)
            # Klien bisa mengirim pesan "ping" secara berkala
            data = await websocket.receive_text()
            logger.debug(f"Menerima pesan ping dari user {user_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error pada koneksi WebSocket user {user_id}: {e}")
        manager.disconnect(user_id)