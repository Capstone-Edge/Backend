from typing import List, Dict, Any

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        websocket: WebSocket,
    ) -> None:
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        disconnected_connections: List[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)

        for connection in disconnected_connections:
            self.disconnect(connection)


ws_manager = WebSocketManager()