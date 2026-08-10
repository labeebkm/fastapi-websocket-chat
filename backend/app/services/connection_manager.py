from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections: list[WebSocket] = []

        self.users: dict[str, WebSocket] = {}

    async def connect(
        self,
        websocket: WebSocket,
        username: str,
    ):

        await websocket.accept()

        self.active_connections.append(websocket)

        self.users[username] = websocket

        print(f"User connected: {username}")

        print(
            f"Total connections: "
            f"{len(self.active_connections)}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
        username: str,
    ):

        if websocket in self.active_connections:

            self.active_connections.remove(websocket)

        if self.users.get(username) == websocket:

            del self.users[username]

        print(f"User disconnected: {username}")

        print(
            f"Total connections: "
            f"{len(self.active_connections)}"
        )

    async def send_personal_message(
        self,
        message: str,
        websocket: WebSocket,
    ):

        await websocket.send_text(message)

    async def send_private_message(
        self,
        receiver: str,
        message: str,
    ) -> bool:

        websocket = self.users.get(receiver)

        if websocket is None:

            return False

        await websocket.send_text(message)

        return True

    async def broadcast(
        self,
        message: str,
    ):

        for connection in self.active_connections:

            await connection.send_text(message)


manager = ConnectionManager()