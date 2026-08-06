from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        print("=" * 50)
        print(f"Connected: {id(websocket)}")
        print(f"Total Connections: {len(self.active_connections)}")
        print("=" * 50)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

        print("=" * 50)
        print(f"Disconnected: {id(websocket)}")
        print(f"Total Connections: {len(self.active_connections)}")
        print("=" * 50)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        print(f"Broadcasting to {len(self.active_connections)} clients")

        for connection in self.active_connections:
            print(f"Sending to {id(connection)}")
            await connection.send_text(message)


manager = ConnectionManager()