import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.events import ChatEvent
from app.services.connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:

        while True:

            data = await websocket.receive_text()

            event = ChatEvent.model_validate_json(data)

            print(f"Received Event: {event}")

            match event.type:

                case "chat":

                    response = {
                        "type": "chat",
                        "sender": "Server",
                        "message": event.message,
                    }

                    await manager.broadcast(
                        json.dumps(response)
                    )

                case _:

                    response = {
                        "type": "error",
                        "sender": "Server",
                        "message": "Unknown event type",
                    }

                    await manager.send_personal_message(
                        json.dumps(response),
                        websocket,
                    )

    except WebSocketDisconnect:

        manager.disconnect(websocket)