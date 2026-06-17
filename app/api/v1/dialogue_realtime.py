from __future__ import annotations

import json
from datetime import datetime
from threading import Lock
from typing import Literal

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/dialogues", tags=["Dialogue Realtime"])

Role = Literal["user", "assistant", "system"]


class DialogueMessage(BaseModel):
    id: int
    session_id: str | None = None
    client_id: str | None = None
    device_id: str | None = None
    role: Role
    source: str | None = None
    text: str
    status: str | None = None
    mode: str | None = None
    clarification_needed: bool | None = None
    timestamp: str


class DialogueRecentResponse(BaseModel):
    messages: list[DialogueMessage]


_dialogue_logs: list[DialogueMessage] = []
_dialogue_ws_connections: list[WebSocket] = []
_lock = Lock()
_next_id = 1
MAX_LOGS = 300


def _make_message_payload(message: DialogueMessage) -> str:
    return json.dumps(
        {
            "type": "dialogue_message",
            "message": message.model_dump(),
        },
        ensure_ascii=False,
    )


async def _broadcast_dialogue_message(message: DialogueMessage):
    payload = _make_message_payload(message)

    disconnected: list[WebSocket] = []

    for websocket in list(_dialogue_ws_connections):
        try:
            await websocket.send_text(payload)
        except Exception:
            disconnected.append(websocket)

    for websocket in disconnected:
        if websocket in _dialogue_ws_connections:
            _dialogue_ws_connections.remove(websocket)


async def append_dialogue_message(
    *,
    role: Role,
    text: str | None,
    session_id: str | None = None,
    client_id: str | None = None,
    device_id: str | None = None,
    source: str | None = None,
    status: str | None = None,
    mode: str | None = None,
    clarification_needed: bool | None = None,
) -> DialogueMessage | None:
    """
    Edge / Frontend ↔ Backend 대화 내용을 메모리에 저장하고
    WebSocket으로 Frontend에 실시간 push한다.

    주의:
    - 현재는 데모용 메모리 저장 방식이다.
    - Backend 재시작 시 로그는 초기화된다.
    """
    global _next_id

    if text is None:
        return None

    clean_text = str(text).strip()

    if not clean_text:
        return None

    with _lock:
        message = DialogueMessage(
            id=_next_id,
            session_id=session_id,
            client_id=client_id,
            device_id=device_id,
            role=role,
            source=source,
            text=clean_text,
            status=status,
            mode=mode,
            clarification_needed=clarification_needed,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

        _next_id += 1
        _dialogue_logs.append(message)

        if len(_dialogue_logs) > MAX_LOGS:
            del _dialogue_logs[: len(_dialogue_logs) - MAX_LOGS]

    await _broadcast_dialogue_message(message)
    return message


@router.get("/recent", response_model=DialogueRecentResponse)
async def get_recent_dialogues(
    limit: int = Query(default=100, ge=1, le=300),
):
    """
    Frontend 초기 로딩용.
    WebSocket 연결 전에 기존 최근 로그를 한 번 가져온다.
    """
    with _lock:
        return DialogueRecentResponse(messages=_dialogue_logs[-limit:])


@router.delete("/recent")
async def clear_recent_dialogues():
    """
    데모 중 채팅 로그 초기화용.
    """
    global _next_id

    with _lock:
        _dialogue_logs.clear()
        _next_id = 1

    return {
        "status": "ok",
        "message": "dialogue logs cleared",
    }


@router.websocket("/ws")
async def dialogue_websocket(websocket: WebSocket):
    """
    Frontend 대화 로그 실시간 수신용 WebSocket.

    접속 주소:
    ws://localhost:8000/api/v1/dialogues/ws
    """
    await websocket.accept()
    _dialogue_ws_connections.append(websocket)

    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "dialogue_snapshot",
                    "messages": [msg.model_dump() for msg in _dialogue_logs[-100:]],
                },
                ensure_ascii=False,
            )
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    except Exception:
        pass

    finally:
        if websocket in _dialogue_ws_connections:
            _dialogue_ws_connections.remove(websocket)