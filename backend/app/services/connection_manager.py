from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections: list[WebSocket] = []

        self.users: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):

        await websocket.accept()

        self.active_connections.append(websocket)

        print(f"Connected ({len(self.active_connections)} clients)")

    def disconnect(self, websocket: WebSocket):

        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        username = None

        for user, ws in self.users.items():
            if ws == websocket:
                username = user
                break

        if username:
            del self.users[username]
            print(f"{username} disconnected")

    def register_user(self, username: str, websocket: WebSocket):

        self.users[username] = websocket

        print(f"Registered: {username}")

        print(self.users)

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
    ):

        websocket = self.users.get(receiver)

        if websocket is None:
            return False

        await websocket.send_text(message)

        return True

    async def broadcast(self, message: str):

        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()