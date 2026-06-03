import json
import os
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

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


class CommandProcessRequest(BaseModel):
    session_id: str | None = None
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
                last_intent
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
):
    db.execute(
        text(
            """
            UPDATE dialogue_sessions
            SET status = :status,
                pending_command = :pending_command,
                clarification_turn = :clarification_turn,
                last_intent = :last_intent,
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

async def _process_clarification_flow(
    db: Session,
    session_id: str,
    user_answer: str,
    pending_info: dict[str, Any],
):
    clarify_result = await clarify_natural_language(
        session_id=session_id,
        user_answer=user_answer,
        pending_command=pending_info["pending_command"],
    )

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
    session_id = request.session_id or f"sess-{uuid4().hex[:8]}"

    # 1. session_id에 pending_command가 있으면,
    #    이 입력은 새 명령이 아니라 재질문 답변으로 처리한다.
    pending_info = _try_load_pending_command(
        db=db,
        session_id=session_id,
    )

    if pending_info is not None:
        return await _process_clarification_flow(
            db=db,
            session_id=session_id,
            user_answer=raw_text,
            pending_info=pending_info,
        )

    # 2. pending_command가 없으면 기존처럼 일반 자연어 명령 parse 수행
    parser_mode = os.getenv("PARSER_MODE", "rule")

    common_args = {
        "raw_text": raw_text,
        "session_id": session_id,
        "device_id": request.device_id,
        "source": request.source or "frontend",
        "db": db,
    }

    if parser_mode == "llm":
        parse_result = await parse_with_llm(**common_args)
    else:
        parse_result = await parse_natural_language(**common_args)

    # 3. 모호한 명령이면 pending_command는 parser 쪽에서 저장되고,
    #    여기서는 재질문 응답만 반환한다.
    if parse_result.get("clarification_needed") is True:
        return {
            "status": "waiting_clarification",
            "mode": "parse",
            **parse_result,
        }

    # 4. 명확한 명령이면 execute까지 자동 실행한다.
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