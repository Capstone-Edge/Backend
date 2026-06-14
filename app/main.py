import json

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import edge
from app.api.v1.command_process import router as command_process_router
from app.api.v1.commands import router as commands_router
from app.api.v1.dialogue_realtime import router as dialogue_realtime_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.routines import router as routines_router
from app.core.state_manager import (
    apply_device_control,
    broadcast_state,
    device_states,
    websocket_connections,
)
from app.core.ws_manager import ws_manager
from app.db.database import get_db


app = FastAPI(title="SmartHome AIoT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_router)
app.include_router(routines_router)
app.include_router(commands_router)
app.include_router(command_process_router)
app.include_router(dialogue_realtime_router)
app.include_router(edge.router)


@app.get("/")
async def root():
    return {"message": "Smart Home AIoT Backend is running!"}


@app.get("/api/v1/db/health")
async def db_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT DATABASE() AS db_name")).mappings().first()

    return {
        "status": "ok",
        "db_name": result["db_name"],
    }



@app.post("/api/v1/command/execute")
async def command_execute(body: dict):
    """
    직접 기기 제어.
    NLU 없이 파라미터를 직접 전달하는 구형 테스트용 endpoint.
    """
    device = body.get("device")
    params = body.get("parameters", {})
    changed = apply_device_control(device, params)

    await broadcast_state()

    return {
        "status": "ok",
        "device": device,
        "changed": changed,
    }


@app.get("/api/v1/devices/state")
async def devices_state():
    return device_states.model_dump()


@app.websocket("/ws/device-states")
async def websocket_device_states(websocket: WebSocket):
    """
    기기 상태 전용 WebSocket.
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

    except Exception:
        ws_manager.disconnect(websocket)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    기존 프론트 호환용 기기 상태 WebSocket.
    """
    await websocket.accept()
    websocket_connections.append(websocket)

    await websocket.send_text(
        json.dumps(
            device_states.model_dump(),
            ensure_ascii=False,
        )
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )