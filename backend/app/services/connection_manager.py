from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        # username -> set of WebSocket connections
        self.active_connections: dict[
            str, set[WebSocket]
        ] = defaultdict(set)

    async def connect(
        self,
        username: str,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.active_connections[username].add(
            websocket
        )

    def disconnect(
        self,
        username: str,
        websocket: WebSocket,
    ):
        connections = self.active_connections.get(username)

        if not connections:
            return

        connections.discard(websocket)

        # Remove username only when all tabs/connections
        # for that user are disconnected.
        if not connections:
            del self.active_connections[username]

    def is_online(self, username: str) -> bool:
        return username in self.active_connections

    def get_online_users(self) -> list[str]:
        return list(self.active_connections.keys())

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket,
    ):
        await websocket.send_text(message)

    async def send_to_user(
        self,
        username: str,
        message: str,
    ):
        connections = self.active_connections.get(username, set())

        for websocket in list(connections):
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(username, websocket)

    async def broadcast(
        self,
        message: str,
    ):
        for username in list(self.active_connections.keys()):
            await self.send_to_user(
                username,
                message,
            )


manager = ConnectionManager()