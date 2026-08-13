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


    # To check whether the user is already connect through another tab
    
    was_online = manager.is_online(username)

    # Register WebSocket connection
    await manager.connect(
        websocket,
        username,
    )

    # Send current online users to the newly connected client
    online_users = manager.get_online_users()

    presence_sync_event = {
        "type": "presence_sync",
        "users": online_users,
    }

    await manager.send_personal_message(
        json.dumps(presence_sync_event),
        websocket,
    )

    # Notify everyone that the user came online
    # Only send this if this is the user's first active connection.
    if not was_online:

        presence_event = {
            "type": "presence",
            "username": username,
            "status": "online",
        }

        await manager.broadcast(
            json.dumps(presence_event)
        )

    try:

        while True:

            data = await websocket.receive_text()

            payload = json.loads(data)

            event_type = payload.get("type")


            match event_type:

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

                    # Receiver is offline
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

        connections = manager.users.get(username)

        had_other_connections = (
            connections is not None
            and len(connections) > 1
        )

        manager.disconnect(
            websocket,
            username,
        )

        if not had_other_connections:

            presence_event = {
                "type": "presence",
                "username": username,
                "status": "offline",
            }

            await manager.broadcast(
                json.dumps(presence_event)
            )