from fastapi import WebSocket

# Manages all active WebSocket connections and their associated user info
class ConnectionManager():
    def __init__(self):
        self.active_connections = []       # list of all connected WebSocket clients
        self.user_connections = {}         # maps each WebSocket to its user info (set after a "join" event)

    # Accept the connection and add it to the tracking structures
    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[websocket] = None  # user info is unknown until they send a "join" event

    # Remove the connection from both tracking structures on disconnect
    def disconnect(self, websocket):
        self.active_connections.remove(websocket)
        self.user_connections.pop(websocket, None)

    # Associate a WebSocket connection with a user's info after they send a "join" event
    def register_user(self, websocket, user_info):
        self.user_connections[websocket] = user_info

    # Send a message to every connected client, optionally skipping one (e.g. the sender for typing events)
    async def broadcast(self, message, exclude = None):
        disconnected = []
        for websocket in self.active_connections:
            if websocket == exclude:
                continue
            try:
                await websocket.send_json(message)
            except Exception:
                # If sending fails the client is gone — collect it for cleanup
                disconnected.append(websocket)
        # Clean up any connections that failed during broadcast
        for websocket in disconnected:
            self.active_connections.remove(websocket)
            self.user_connections.pop(websocket, None)

# Single shared instance used across all routes
manager = ConnectionManager()
