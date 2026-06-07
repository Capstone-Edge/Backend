import json
import logging
import os
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import get_db
from app.ai_mcp.parser import parse_natural_language
from app.ai_mcp.llm_parser import parse_with_llm
from app.ai_mcp.clarifier import clarify_natural_language
from app.api.v1.commands import (
    CommandItem,
    ExecuteCommandRequest,
    execute_commands,
)

router = APIRouter(prefix="/api/v1/commands", tags=["Command Pipeline"])

PENDING_TTL_SECONDS = 30

CANCEL_WORDS = [
    "취소",
    "취소해",
    "그만",
    "그만해",
    "됐어",
    "됐습니다",
    "아니야",
    "안 해",
    "안해",
    "하지마",
    "필요없어",
    "필요 없어",
]

DEVICE_KEYWORDS = {
    "air_conditioner": ["에어컨", "냉방", "난방", "제습"],
    "light": ["불", "조명", "전등", "등"],
    "tv": ["tv", "TV", "티비", "텔레비전"],
    "robot_vacuum": ["청소기", "로봇청소기", "청소"],
    "air_purifier": ["공기청정기", "공청기"],
    "washing_machine": ["세탁기", "빨래"],
    "oven": ["오븐"],
}

class CommandProcessRequest(BaseModel):
    session_id: str | None = None
    client_id: str | None = None
    device_id: str
    raw_text: str | None = None
    stt_text: str | None = None
    source: str | None = "frontend"

class CommandProcessClarifyRequest(BaseModel):
    session_id: str
    user_answer: str


def _pick_raw_text(request: CommandProcessRequest) -> str:
    raw_text = request.raw_text or request.stt_text

    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="raw_text 또는 stt_text가 필요합니다.",
        )

    return raw_text.strip()

def _generate_session_id() -> str:
    return f"sess-{uuid4().hex[:8]}"


def _find_recent_pending_session_by_client_id(
    db: Session,
    client_id: str | None,
) -> str | None:
    if not client_id:
        return None

    row = db.execute(
        text(
            """
            SELECT
                session_id
            FROM dialogue_sessions
            WHERE client_id = :client_id
              AND pending_command IS NOT NULL
              AND status IN ('pending', 'waiting_clarification')
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"client_id": client_id},
    ).mappings().first()

    if not row:
        return None

    # TTL 검사는 기존 _try_load_pending_command()에서 다시 수행한다.
    pending_info = _try_load_pending_command(
        db=db,
        session_id=row["session_id"],
    )

    if pending_info is None:
        return None

    return row["session_id"]


def _resolve_session_id(
    db: Session,
    request: CommandProcessRequest,
) -> str:
    if request.session_id and request.session_id.strip():
        return request.session_id.strip()

    recovered_session_id = _find_recent_pending_session_by_client_id(
        db=db,
        client_id=request.client_id,
    )

    if recovered_session_id:
        return recovered_session_id

    return _generate_session_id()

def _get_pending_device_type(pending_command: dict[str, Any]) -> str | None:
    if not pending_command:
        return None

    device_type = pending_command.get("device_type")
    if device_type:
        return device_type

    target_devices = pending_command.get("target_devices")
    if isinstance(target_devices, list) and target_devices:
        first_target = target_devices[0]
        if isinstance(first_target, dict):
            return first_target.get("device_type") or first_target.get("device")

    commands = pending_command.get("commands")
    if isinstance(commands, list) and commands:
        first_command = commands[0]
        if isinstance(first_command, dict):
            return first_command.get("device_type")

    return None

def _is_cancel_pending_text(raw_text: str) -> bool:
    normalized = raw_text.strip().lower()
    return any(word.lower() in normalized for word in CANCEL_WORDS)

def _detect_device_type_from_text(raw_text: str) -> str | None:
    normalized = raw_text.strip()

    for device_type, keywords in DEVICE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                return device_type

    return None


def _detect_all_device_types_from_text(raw_text: str) -> list[str]:
    normalized = raw_text.strip()
    detected: list[str] = []
    for device_type, keywords in DEVICE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                detected.append(device_type)
                break
    return detected


def _is_new_command_different_from_pending(
    raw_text: str,
    pending_command: dict[str, Any],
) -> bool:
    pending_device_type = _get_pending_device_type(pending_command)
    all_detected = _detect_all_device_types_from_text(raw_text)

    if not all_detected:
        return False

    # 여러 기기가 감지되면 복합 명령 → 새 파서로 전환
    if len(all_detected) > 1:
        return True

    # pending 기기를 특정할 수 없는 상태(unknown pending)이고 사용자가 명확한 기기를 언급하면 새 명령으로 처리
    if not pending_device_type:
        return True

    return all_detected[0] != pending_device_type

def _try_load_pending_command(
    db: Session,
    session_id: str,
) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT
                session_id,
                pending_command,
                clarification_turn,
                last_intent,
                updated_at
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    if not row:
        return None

    if not row["pending_command"]:
        return None

    updated_at = row["updated_at"]

    if updated_at:
        now = datetime.now()

        if updated_at.tzinfo is not None:
            now = datetime.now(updated_at.tzinfo)

        elapsed = now - updated_at

        if elapsed > timedelta(seconds=PENDING_TTL_SECONDS):
            _expire_pending_command(
                db=db,
                session_id=session_id,
                last_intent=row["last_intent"] or "device_control",
            )
            return None

    pending_command = row["pending_command"]

    if isinstance(pending_command, str):
        pending_command = json.loads(pending_command)

    return {
        "session_id": row["session_id"],
        "pending_command": pending_command,
        "clarification_turn": row["clarification_turn"] or 1,
        "last_intent": row["last_intent"] or "device_control",
    }

def _load_pending_command(db: Session, session_id: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT
                session_id,
                pending_command,
                clarification_turn,
                last_intent
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
            """
        ),
        {"session_id": session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="해당 session_id의 대화 세션을 찾을 수 없습니다.",
        )

    if not row["pending_command"]:
        raise HTTPException(
            status_code=404,
            detail="해당 세션에 pending_command가 없습니다.",
        )

    pending_command = row["pending_command"]

    if isinstance(pending_command, str):
        pending_command = json.loads(pending_command)

    return {
        "session_id": row["session_id"],
        "pending_command": pending_command,
        "clarification_turn": row["clarification_turn"] or 1,
        "last_intent": row["last_intent"] or "device_control",
    }

def _update_pending_command(
    db: Session,
    session_id: str,
    pending_command: dict[str, Any],
    clarification_turn: int,
    last_intent: str,
    client_id: str | None = None,
    source: str | None = None,
):
    db.execute(
        text(
            """
            UPDATE dialogue_sessions
            SET status = :status,
                pending_command = :pending_command,
                clarification_turn = :clarification_turn,
                last_intent = :last_intent,
                client_id = COALESCE(:client_id, client_id),
                source = COALESCE(:source, source),
                updated_at = NOW()
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
            "status": "pending",
            "pending_command": json.dumps(pending_command, ensure_ascii=False),
            "clarification_turn": clarification_turn,
            "last_intent": last_intent,
            "client_id": client_id,
            "source": source,
        },
    )

    db.commit()

def _attach_client_to_session(
    db: Session,
    session_id: str,
    client_id: str | None,
    source: str | None,
):
    db.execute(
        text(
            """
            UPDATE dialogue_sessions
            SET client_id = COALESCE(:client_id, client_id),
                source = COALESCE(:source, source),
                updated_at = NOW()
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
            "client_id": client_id,
            "source": source,
        },
    )

    db.commit()

def _clear_pending_command(
    db: Session,
    session_id: str,
    last_intent: str,
):
    db.execute(
        text(
            """
            UPDATE dialogue_sessions
            SET status = :status,
                pending_command = NULL,
                clarification_turn = 0,
                last_intent = :last_intent,
                updated_at = NOW()
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
            "status": "active",
            "last_intent": last_intent,
        },
    )

    db.commit()

def _cancel_pending_response(
    db: Session,
    session_id: str,
    pending_info: dict[str, Any],
):
    _clear_pending_command(
        db=db,
        session_id=session_id,
        last_intent=pending_info.get("last_intent", "device_control"),
    )

    return {
        "status": "cancelled",
        "mode": "cancel_pending",
        "session_id": session_id,
        "clarification_needed": False,
        "response_text": "이전 요청을 취소했어요.",
    }

def _expire_pending_command(
    db: Session,
    session_id: str,
    last_intent: str = "device_control",
):
    db.execute(
        text(
            """
            UPDATE dialogue_sessions
            SET status = :status,
                pending_command = NULL,
                clarification_turn = 0,
                last_intent = :last_intent,
                updated_at = NOW()
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
            "status": "expired",
            "last_intent": last_intent,
        },
    )

    db.commit()

async def _execute_from_parse_result(
    db: Session,
    session_id: str,
    raw_user_input: str,
    parse_result: dict[str, Any],
):
    commands = parse_result.get("commands", [])

    if not commands:
        raise HTTPException(
            status_code=400,
            detail="clarification_needed=false 이지만 실행할 commands가 없습니다.",
        )

    execute_request = ExecuteCommandRequest(
        session_id=session_id,
        raw_user_input=raw_user_input,
        intent=parse_result.get("intent", "device_control"),
        commands=[CommandItem(**command) for command in commands],
        response_text=parse_result.get("response_text", ""),
    )

    return await execute_commands(
        request=execute_request,
        db=db,
    )

async def _process_parse_flow(
    db: Session,
    session_id: str,
    device_id: str,
    raw_text: str,
    source: str,
    client_id: str | None = None,
):
    parser_mode = os.getenv("PARSER_MODE", "rule")

    common_args = {
        "raw_text": raw_text,
        "session_id": session_id,
        "device_id": device_id,
        "source": source,
        "db": db,
    }

    if parser_mode == "llm":
        parse_result = await parse_with_llm(**common_args)
    else:
        parse_result = await parse_natural_language(**common_args)

    _attach_client_to_session(
        db=db,
        session_id=parse_result["session_id"],
        client_id=client_id,
        source=source,
    )

    if parse_result.get("clarification_needed") is True:
        # 즉시 실행 가능한 commands가 있으면 먼저 실행 후 재질문
        immediate_commands = parse_result.get("commands", [])
        execute_result = None
        if immediate_commands:
            try:
                execute_result = await _execute_from_parse_result(
                    db=db,
                    session_id=parse_result["session_id"],
                    raw_user_input=raw_text,
                    parse_result=parse_result,
                )
                logger.info(f"[PARSE FLOW] 즉시 실행 완료: {[c['tool_name'] for c in immediate_commands]}")
            except Exception as e:
                logger.error(f"[PARSE FLOW] 즉시 실행 실패: {e}")
                # 실행 실패해도 재질문은 계속 진행
        return {
            "status": "waiting_clarification",
            "mode": "parse",
            "execute_result": execute_result,
            **parse_result,
        }

    # 정보 조회 응답 (commands 없이 response_text만 있는 경우)
    if not parse_result.get("commands"):
        return {
            "status": "info_response",
            "mode": "parse",
            "session_id": parse_result["session_id"],
            "clarification_needed": False,
            "response_text": parse_result.get("response_text", ""),
            "parse_result": parse_result,
        }

    execute_result = await _execute_from_parse_result(
        db=db,
        session_id=parse_result["session_id"],
        raw_user_input=raw_text,
        parse_result=parse_result,
    )

    return {
        "status": "executed",
        "mode": "parse",
        "session_id": parse_result["session_id"],
        "clarification_needed": False,
        "response_text": parse_result.get("response_text", ""),
        "parse_result": parse_result,
        "execute_result": execute_result,
    }

async def _process_clarification_flow(
    db: Session,
    session_id: str,
    user_answer: str,
    pending_info: dict[str, Any],
):
    logger.info(f"[CLARIFY FLOW] 진입 — session_id={session_id}, user_answer={user_answer}")

    clarify_result = await clarify_natural_language(
        session_id=session_id,
        user_answer=user_answer,
        pending_command=pending_info["pending_command"],
    )

    logger.info(f"[CLARIFY FLOW] clarify_result clarification_needed={clarify_result.get('clarification_needed')}, commands={clarify_result.get('commands')}")

    if clarify_result.get("clarification_needed") is True:
        _update_pending_command(
            db=db,
            session_id=session_id,
            pending_command=clarify_result.get("pending_command") or pending_info["pending_command"],
            clarification_turn=clarify_result.get(
                "clarification_turn",
                pending_info["clarification_turn"] + 1,
            ),
            last_intent=clarify_result.get("intent", pending_info["last_intent"]),
        )

        return {
            "status": "waiting_clarification",
            "mode": "clarify",
            **clarify_result,
        }

    execute_result = await _execute_from_parse_result(
        db=db,
        session_id=session_id,
        raw_user_input=user_answer,
        parse_result=clarify_result,
    )

    from app.core.state_manager import broadcast_state, websocket_connections, device_states
    logger.info(f"[CLARIFY BROADCAST] websocket_connections 수: {len(websocket_connections)}")
    logger.info(f"[CLARIFY BROADCAST] device_states: {device_states.model_dump()}")
    await broadcast_state()

    _clear_pending_command(
        db=db,
        session_id=session_id,
        last_intent=clarify_result.get("intent", pending_info["last_intent"]),
    )

    return {
        "status": "executed",
        "mode": "clarify",
        "session_id": session_id,
        "clarification_needed": False,
        "response_text": clarify_result.get("response_text", ""),
        "clarify_result": clarify_result,
        "execute_result": execute_result,
    }

@router.post("/process")
async def process_command(
    request: CommandProcessRequest,
    db: Session = Depends(get_db),
):
    raw_text = _pick_raw_text(request)
    session_id = _resolve_session_id(
        db=db,
        request=request,
    )
    source = request.source or "frontend"

    pending_info = _try_load_pending_command(
        db=db,
        session_id=session_id,
    )

    if pending_info is not None:
        pending_command = pending_info["pending_command"]

        # 1. 사용자가 재질문 흐름을 취소한 경우
        if _is_cancel_pending_text(raw_text):
            return _cancel_pending_response(
                db=db,
                session_id=session_id,
                pending_info=pending_info,
            )

        # 2. 사용자가 재질문 답변 대신 다른 기기 명령을 말한 경우
        if _is_new_command_different_from_pending(
            raw_text=raw_text,
            pending_command=pending_command,
        ):
            _clear_pending_command(
                db=db,
                session_id=session_id,
                last_intent=pending_info.get("last_intent", "device_control"),
            )

            parse_response = await _process_parse_flow(
                db=db,
                session_id=_generate_session_id(),
                device_id=request.device_id,
                raw_text=raw_text,
                source=source,
                client_id=request.client_id,
            )

            parse_response["mode"] = "new_command_after_pending_cancelled"
            parse_response["cancelled_pending"] = pending_command

            original_response_text = parse_response.get("response_text", "")
            parse_response["response_text"] = (
                f"이전 요청은 취소하고, {original_response_text}"
                if original_response_text
                else "이전 요청은 취소하고 새 명령을 처리했어요."
            )

            return parse_response

        # 3. 취소도 아니고 다른 기기 명령도 아니면 기존 재질문 답변으로 처리
        return await _process_clarification_flow(
            db=db,
            session_id=session_id,
            user_answer=raw_text,
            pending_info=pending_info,
        )

    # 4. pending_command가 없으면 일반 명령 처리
    return await _process_parse_flow(
        db=db,
        session_id=session_id,
        device_id=request.device_id,
        raw_text=raw_text,
        source=source,
        client_id=request.client_id,
    )

@router.post("/process-clarify")
async def process_command_clarify(
    request: CommandProcessClarifyRequest,
    db: Session = Depends(get_db),
):
    pending_info = _load_pending_command(
        db=db,
        session_id=request.session_id,
    )

    return await _process_clarification_flow(
        db=db,
        session_id=request.session_id,
        user_answer=request.user_answer,
        pending_info=pending_info,
    )