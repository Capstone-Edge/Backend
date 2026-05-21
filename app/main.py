import json
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.state_manager import device_states, websocket_connections, apply_device_control, broadcast_state
from app.services.ai_service import parse_command, clarify_command
from app.mcp.server import mcp, control_air_conditioner, control_tv, control_air_purifier, control_robot_vacuum
import app.services.dialogue_service as dm

# ✨ 1. 새로 만든 edge 라우터 import
from app.api.v1 import edge 

# SQLAlchemy 관련 imports (db 연결용)
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db

# 라우터 import (새로 만든 MCP 라우터, 기존 MCP 라우터는 그대로 유지)
from app.api.v1.mcp import router as mcp_router

# 라우터 import (새로 만든 routines 라우터)
from app.api.v1.routines import router as routines_router

# 라우터 import (새로 만든 commands 라우터)
from app.api.v1.commands import router as commands_router

from app.core.ws_manager import ws_manager

# ─── 요청/응답 모델 (아직 분리 안 된 구형 모델들) ───────────────

class ClarifyRequest(BaseModel):
    text: str
    session_id: str
    context_trigger: str

# ─── FastAPI 앱 ───────────────────────────────────────

app = FastAPI(title="SmartHome AIoT API")

app.include_router(mcp_router) # 기존 MCP 라우터 등록
app.include_router(routines_router) # 새로 만든 Routines 라우터 등록
app.include_router(commands_router) # 새로 만든 Commands 라우터 등록

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✨ 2. 라우터 등록 (기존 /parse 엔드포인트는 edge.py가 대신 처리합니다)
app.include_router(edge.router)

@app.get("/")
async def root():
    return {"message": "Smart Home AIoT Backend is running!"}

# ----------------------------------------------------
@app.get("/api/v1/db/health")
async def db_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT DATABASE() AS db_name")).mappings().first()

    return {
        "status": "ok",
        "db_name": result["db_name"]
    }

# ─── 기기 제어 실행 헬퍼 ───────────────────────────────────

async def execute_nlu_result(nlu: dict):
    """NLU 파싱 결과를 실제 기기 제어로 실행"""
    if nlu.get("clarification_needed"):
        return

    for td in nlu.get("target_devices", []):
        device = td.get("device")
        action = td.get("action")
        params = td.get("parameters", {})

        if device == "air_conditioner":
            await control_air_conditioner(
                power=params.get("power"),
                temperature=params.get("temperature"),
                mode=params.get("mode"),
                fan_speed=params.get("fan_speed"),
                louver_angle=params.get("louver_angle"),
            )
        elif device == "tv":
            await control_tv(
                power=params.get("power"),
                channel=params.get("channel"),
                content_name=params.get("content_name"),
            )
        elif device == "air_purifier":
            await control_air_purifier(
                power=params.get("power"),
                mode=params.get("mode"),
            )
        elif device == "robot_vacuum":
            rv_action = action
            if action in ("start_cleaning", "pause", "return_to_dock"):
                rv_action = action
            elif params.get("power") == "on" or params.get("zone") is not None:
                rv_action = "start_cleaning"
            elif params.get("power") == "off":
                rv_action = "return_to_dock"
            else:
                rv_action = params.get("action")
            await control_robot_vacuum(
                action=rv_action,
                zone=params.get("zone"),
                suction_power=params.get("suction_power"),
                cleaning_mode=params.get("cleaning_mode"),
            )

# ─── 엔드포인트 (아직 분리 안 된 나머지 기능들) ───────────────────

@app.post("/api/v1/dialogue/clarify")
async def dialogue_clarify(req: ClarifyRequest):
    """재질문 답변 처리"""
    history = dm.get_history(req.session_id)

    nlu = await clarify_command(req.text, req.context_trigger, history)

    dm.update_session_history(req.session_id, "user", req.text)
    dm.update_session_history(req.session_id, "assistant", json.dumps(nlu, ensure_ascii=False))

    if not nlu.get("clarification_needed"):
        dm.clear_pending_clarification(req.session_id)
        await execute_nlu_result(nlu)
    else:
        dm.set_pending_clarification(req.session_id, nlu.get("context_trigger", ""))

    return {"session_id": req.session_id, "nlu": nlu}

@app.post("/api/v1/command/execute")
async def command_execute(body: dict):
    """직접 기기 제어 (NLU 없이 파라미터 직접 전달)"""
    device = body.get("device")
    params = body.get("parameters", {})
    changed = apply_device_control(device, params)
    await broadcast_state()
    return {"status": "ok", "device": device, "changed": changed}

@app.get("/api/v1/devices/state")
async def devices_state():
    """전체 기기 상태 반환"""
    return device_states.model_dump()


@app.websocket("/ws/device-states")
async def websocket_device_states(websocket: WebSocket):
    """
    Frontend 기기 상태 실시간 동기화용 WebSocket endpoint.

    연결된 클라이언트는 /api/v1/commands/execute 실행 후
    device_state_update 메시지를 수신한다.
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
    await websocket.accept()
    websocket_connections.append(websocket)
    # 연결 즉시 현재 상태 전송
    await websocket.send_text(json.dumps(device_states.model_dump()))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

    
@app.websocket("/ws/device-states")
async def websocket_device_states(websocket: WebSocket):
    """
    Frontend 기기 상태 실시간 동기화용 WebSocket endpoint.

    연결된 클라이언트는 /api/v1/commands/execute 실행 후
    device_state_update 메시지를 수신한다.
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # 클라이언트 연결 유지용 receive.
            # Frontend가 ping 또는 임의 메시지를 보내면 여기서 수신된다.
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

    except Exception:
        ws_manager.disconnect(websocket)