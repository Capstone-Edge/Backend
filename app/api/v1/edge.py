from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

import json
import re
from typing import Any

import os

from app.ai_mcp.llm_parser import parse_with_llm

import httpx

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.ai_mcp.parser import parse_natural_language
from app.ai_mcp.clarifier import clarify_natural_language

# ✨ Clarify 관련 DTO들도 함께 import 해주어야 합니다.
from app.schemas.edge_dto import (
    CommandRequest, 
    CommandResponse, 
    ClarifyRequest, 
    ClarifyResponse
)

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
    print(f"[/parse] Device: {request.device_id}, Text: {request.stt_text}")

    parser_mode = os.getenv("PARSER_MODE", "rule")

    common_args = {
        "raw_text": request.stt_text,
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
    
# 2. 재질문 답변 처리 (추가된 부분)
@router.post("/dialogues/clarify")
async def clarify_dialogue(
    request: ClarifyRequest,
    db: Session = Depends(get_db),
):
    # 1. 기존 세션 조회
    row = db.execute(
        text("""
            SELECT
                session_id,
                pending_command,
                clarification_turn,
                last_intent
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
        """),
        {"session_id": request.session_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No dialogue session found"
        )

    if not row["pending_command"]:
        raise HTTPException(
            status_code=404,
            detail="No pending command found"
        )

    # 2. pending_command JSON 파싱
    pending_command = row["pending_command"]

    if isinstance(pending_command, str):
        pending_command = json.loads(pending_command)

    # 3. 사용자 답변에서 온도 추출
    match = re.search(r"(\d{2})\s*도", request.user_answer)

    if not match:
        return {
            "session_id": request.session_id,
            "intent": row["last_intent"] or "device_control",
            "commands": [],
            "clarification_needed": True,
            "clarification_turn": (row["clarification_turn"] or 1) + 1,
            "clarification_question": "몇 도로 맞춰드릴까요?",
            "pending_command": pending_command,
            "response_text": "몇 도로 맞춰드릴까요?",
        }

    temperature = int(match.group(1))

    # 4. pending_command 기반 최종 commands 생성
    device_name = pending_command.get("device_name", "living_room_aircon")
    device_type = pending_command.get("device_type", "air_conditioner")
    known_parameters = pending_command.get("known_parameters", {})

    commands = []
    step_order = 1

    if "power" in known_parameters:
        commands.append({
            "step_order": step_order,
            "device_name": device_name,
            "device_type": device_type,
            "tool_name": f"{device_type}.set_power",
            "parameters": {
                "power": known_parameters["power"]
            },
        })
        step_order += 1

    if "mode" in known_parameters:
        commands.append({
            "step_order": step_order,
            "device_name": device_name,
            "device_type": device_type,
            "tool_name": f"{device_type}.set_mode",
            "parameters": {
                "mode": known_parameters["mode"]
            },
        })
        step_order += 1

    commands.append({
        "step_order": step_order,
        "device_name": device_name,
        "device_type": device_type,
        "tool_name": f"{device_type}.set_temperature",
        "parameters": {
            "temperature": temperature
        },
    })

    response_text = f"거실 에어컨을 {temperature}도 냉방으로 켤게요."

    # 5. 세션 상태 초기화
    db.execute(
        text("""
            UPDATE dialogue_sessions
            SET status = :status,
                pending_command = NULL,
                clarification_turn = 0,
                last_intent = :last_intent,
                updated_at = NOW()
            WHERE session_id = :session_id
        """),
        {
            "session_id": request.session_id,
            "status": "active",
            "last_intent": row["last_intent"] or "device_control",
        },
    )

    db.commit()

    return {
        "session_id": request.session_id,
        "intent": row["last_intent"] or "device_control",
        "commands": commands,
        "clarification_needed": False,
        "clarification_turn": 0,
        "clarification_question": None,
        "pending_command": None,
        "response_text": response_text,
    }


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



