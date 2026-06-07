from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

import json
from typing import Any

import os

from app.ai_mcp.llm_parser import parse_with_llm

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ai_mcp.parser import parse_natural_language
from app.ai_mcp.clarifier import clarify_natural_language

from app.schemas.edge_dto import CommandRequest

from pydantic import BaseModel
from sqlalchemy import text


# 스프링의 @RequestMapping("/api/v1/commands")와 같은 역할
router = APIRouter(prefix="/api/v1", tags=["Edge Communication"])

class ClarifyRequest(BaseModel):
    session_id: str
    user_answer: str

# 1. 초기 명령 파싱
@router.post("/commands/parse")
async def parse_command(
    request: CommandRequest,
    db: Session = Depends(get_db),
):
    print(f"[/parse] Device: {request.device_id}, Text: {request.raw_text}")

    parser_mode = os.getenv("PARSER_MODE", "rule")

    common_args = {
        "raw_text": request.raw_text,
        "session_id": request.session_id,
        "device_id": request.device_id,
        "source": request.source or "edge",
        "db": db,
    }

    if parser_mode == "llm":
        result = await parse_with_llm(**common_args)
    else:
        result = await parse_natural_language(**common_args)

    return result
    
# 2. 재질문 답변 처리
@router.post("/dialogues/clarify")
async def clarify_dialogue(
    request: ClarifyRequest,
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            SELECT session_id, pending_command, clarification_turn, last_intent
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
        """),
        {"session_id": request.session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="No dialogue session found")

    if not row["pending_command"]:
        raise HTTPException(status_code=404, detail="No pending command found")

    pending_command = row["pending_command"]
    if isinstance(pending_command, str):
        pending_command = json.loads(pending_command)

    result = await clarify_natural_language(
        session_id=request.session_id,
        user_answer=request.user_answer,
        pending_command=pending_command,
        clarification_turn=row["clarification_turn"] or 1,
    )

    if result.get("clarification_needed"):
        db.execute(
            text("""
                UPDATE dialogue_sessions
                SET clarification_turn = :turn,
                    updated_at = NOW()
                WHERE session_id = :session_id
            """),
            {
                "session_id": request.session_id,
                "turn": (row["clarification_turn"] or 1) + 1,
            },
        )
    else:
        db.execute(
            text("""
                UPDATE dialogue_sessions
                SET status = 'active',
                    pending_command = NULL,
                    clarification_turn = 0,
                    updated_at = NOW()
                WHERE session_id = :session_id
            """),
            {"session_id": request.session_id},
        )
    db.commit()

    return result


# @router.post("/dialogues/clarify-and-execute")
# async def clarify_and_execute_dialogue(request: dict):
#     try:
#         result = await request_clarify_and_execute_to_ai_mcp(request)
#         return result

#     except httpx.HTTPStatusError as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"AI/MCP Server returned error: {e.response.text}",
#         )

#     except httpx.HTTPError as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"AI/MCP Server connection failed: {str(e)}",
#         )



