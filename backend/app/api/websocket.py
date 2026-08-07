import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.events import (
    ChatEvent,
    PrivateChatEvent,
    RegisterEvent,
)
from app.services.connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:

        while True:

            data = await websocket.receive_text()

            payload = json.loads(data)

            event_type = payload.get("type")

            match event_type:

                # -------------------------
                # Register User
                # -------------------------
                case "register":

                    event = RegisterEvent.model_validate(payload)

                    manager.register_user(
                        event.username,
                        websocket,
                    )

                    response = {
                        "type": "register",
                        "sender": "Server",
                        "message": f"{event.username} registered successfully",
                    }

                    await manager.send_personal_message(
                        json.dumps(response),
                        websocket,
                    )

                # -------------------------
                # Broadcast Chat
                # -------------------------
                case "chat":

                    event = ChatEvent.model_validate(payload)

                    response = {
                        "type": "chat",
                        "sender": event.username,
                        "message": event.message,
                    }

                    await manager.broadcast(
                        json.dumps(response)
                    )

                # -------------------------
                # Private Chat
                # -------------------------
                case "private_chat":

                    event = PrivateChatEvent.model_validate(payload)

                    response = {
                        "type": "private_chat",
                        "sender": event.username,
                        "message": event.message,
                    }

                    sent = await manager.send_private_message(
                        receiver=event.receiver,
                        message=json.dumps(response),
                    )

                    if not sent:

                        error = {
                            "type": "error",
                            "sender": "Server",
                            "message": f"{event.receiver} is not online",
                        }

                        await manager.send_personal_message(
                            json.dumps(error),
                            websocket,
                        )

                # -------------------------
                # Unknown Event
                # -------------------------
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