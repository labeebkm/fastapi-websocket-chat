from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()

            print(f"Received from {id(websocket)}: {message}")

            await manager.broadcast(f"Broadcast: {message}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)