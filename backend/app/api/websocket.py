import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.security import decode_access_token
from app.schemas.events import (
    ChatEvent,
    PrivateChatEvent,
)
from app.services.connection_manager import manager


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    token = websocket.query_params.get("token")

    if not token:

        await websocket.close(code=1008)

        return

    username = decode_access_token(token)

    if username is None:

        await websocket.close(code=1008)

        return

    await manager.connect(
        websocket,
        username,
    )

    try:

        while True:

            data = await websocket.receive_text()

            payload = json.loads(data)

            event_type = payload.get("type")

            match event_type:

                # -------------------------
                # Broadcast Chat
                # -------------------------

                case "chat":

                    event = ChatEvent.model_validate(
                        payload
                    )

                    response = {
                        "type": "chat",
                        "sender": username,
                        "message": event.message,
                    }

                    await manager.broadcast(
                        json.dumps(response)
                    )

                # -------------------------
                # Private Chat
                # -------------------------

                case "private_chat":

                    event = PrivateChatEvent.model_validate(
                        payload
                    )

                    response = {
                        "type": "private_chat",
                        "sender": username,
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
                            "message": (
                                f"{event.receiver} "
                                "is not online"
                            ),
                        }

                        await manager.send_personal_message(
                            json.dumps(error),
                            websocket,
                        )

                # -------------------------
                # Unknown Event
                # -------------------------

                case _:

                    error = {
                        "type": "error",
                        "sender": "Server",
                        "message": "Unknown event type",
                    }

                    await manager.send_personal_message(
                        json.dumps(error),
                        websocket,
                    )

    except WebSocketDisconnect:

        manager.disconnect(
            websocket,
            username,
        )