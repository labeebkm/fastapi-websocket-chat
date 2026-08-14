import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.security import decode_access_token
from app.db.database import SessionLocal
from app.schemas.events import (
    ChatEvent,
    PrivateChatEvent,
    GetChatHistoryEvent,
)
from app.services import chat_service
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

                    # Persist the message regardless of whether
                    # the receiver is currently online.
                    with SessionLocal() as db:
                        try:
                            chat_service.save_message(
                                db,
                                sender_username=username,
                                receiver_username=event.receiver,
                                content=event.message,
                            )
                        except ValueError:
                            error = {
                                "type": "error",
                                "sender": "Server",
                                "message": f"{event.receiver} does not exist",
                            }
                            await manager.send_personal_message(
                                json.dumps(error),
                                websocket,
                            )
                            continue

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


                case "get_chat_history":

                    event = GetChatHistoryEvent.model_validate(
                        payload
                    )

                    with SessionLocal() as db:
                        history, has_more = chat_service.get_message_history(
                            db,
                            user_a=username,
                            user_b=event.receiver,
                            before_id=event.before_id,
                            limit=event.limit,
                        )

                        messages = [
                            {
                                "id": msg.id,
                                "sender": msg.sender.username,
                                "receiver": msg.receiver.username,
                                "message": msg.content,
                                "created_at": msg.created_at.isoformat(),
                            }
                            for msg in history
                        ]

                    response = {
                        "type": "chat_history",
                        "messages": messages,
                        "has_more": has_more,
                        # send this back as the next before_id for
                        # "load older messages"
                        "oldest_id": messages[0]["id"] if messages else None,
                    }

                    await manager.send_personal_message(
                        json.dumps(response),
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

        connections = manager.active_connections.get(username)

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