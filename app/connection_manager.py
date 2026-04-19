from fastapi import WebSocket

class ConnectionManager():
    def __init__(self):
        self.active_connections = []
        self.user_connections = {}

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[websocket] = None

    def disconnect(self, websocket):
        self.active_connections.remove(websocket)
        self.user_connections.pop(websocket, None)

    def register_user(self, websocket, user_info):
        self.user_connections[websocket] = user_info

    async def broadcast(self, message, exclude = None):
        disconnected = []
        for websocket in self.active_connections:
            if websocket == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.active_connections.remove(websocket)
            self.user_connections.pop(websocket, None)
                
manager = ConnectionManager()