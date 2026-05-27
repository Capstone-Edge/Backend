import json
import os
import re
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from app.api.v1.mcp import get_mcp_tools, get_mcp_device_states
from app.api.v1.routines import get_routines
from app.ai_mcp.prompt import AI_PARSER_SYSTEM_PROMPT
from app.ai_mcp.validator import validate_llm_parse_result
from app.ai_mcp.session_store import save_parse_session

load_dotenv()


def _extract_text_from_claude_response(message) -> str:
    """
    Claude Messages API 응답에서 text 블록만 추출한다.
    """
    parts = []

    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)

    return "\n".join(parts).strip()


def _safe_json_loads(text: str) -> dict[str, Any]:
    """
    Claude가 혹시 ```json 코드블록으로 감싸서 반환해도 JSON만 파싱한다.
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = (
            cleaned
            .replace("```json", "")
            .replace("```JSON", "")
            .replace("```", "")
            .strip()
        )

    return json.loads(cleaned)

def _is_ambiguous_hot_request(raw_text: str) -> bool:
    has_hot_expression = any(keyword in raw_text for keyword in ["덥", "더워", "시원하게"])
    has_temperature = re.search(r"\d{2}\s*도", raw_text) is not None
    has_explicit_aircon_action = "에어컨" in raw_text and ("켜" in raw_text or "꺼" in raw_text)

    return has_hot_expression and not has_temperature and not has_explicit_aircon_action


def _build_hot_clarification_result(effective_session_id: str) -> dict[str, Any]:
    return {
        "session_id": effective_session_id,
        "intent": "device_control",
        "commands": [],
        "clarification_needed": True,
        "clarification_turn": 1,
        "clarification_question": "에어컨을 몇 도로 맞춰드릴까요?",
        "pending_command": {
            "device_name": "living_room_aircon",
            "device_type": "air_conditioner",
            "inferred_intent": "cooling",
            "context_trigger": "hot",
            "candidate_tools": [
                "air_conditioner.set_power",
                "air_conditioner.set_mode",
                "air_conditioner.set_temperature",
            ],
            "known_parameters": {
                "power": "on",
                "mode": "cool",
            },
            "missing_parameters": ["temperature"],
        },
        "response_text": "에어컨을 몇 도로 맞춰드릴까요?",
    }


async def parse_with_llm(
    raw_text: str,
    session_id: str | None = None,
    device_id: str | None = None,
    source: str | None = "edge",
    db=None,
) -> dict[str, Any]:
    effective_session_id = session_id or "mock-session-001"

    if _is_ambiguous_hot_request(raw_text):
        forced_result = _build_hot_clarification_result(effective_session_id)

        save_parse_session(
            db=db,
            session_id=effective_session_id,
            intent=forced_result["intent"],
            clarification_needed=forced_result["clarification_needed"],
            pending_command=forced_result["pending_command"],
            clarification_turn=forced_result["clarification_turn"],
        )

        return forced_result

    tools_data = get_mcp_tools(
        device_type=None,
        is_active=True,
        db=db,
    )

    states_data = get_mcp_device_states(
        device_name=None,
        device_type=None,
        location=None,
        is_active=True,
        db=db,
    )

    routines_data = get_routines(
        is_active=True,
        db=db,
    )

    user_payload = {
        "user_input": raw_text,
        "session_id": effective_session_id,
        "device_id": device_id,
        "source": source,
        "mcp_tools": tools_data,
        "device_states": states_data,
        "routines": routines_data,
    }

    client = Anthropic()
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    message = client.messages.create(
        model=model_name,
        max_tokens=1200,
        temperature=0,
        system=AI_PARSER_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            }
        ],
    )

    raw_output = _extract_text_from_claude_response(message)

    try:
        parsed = _safe_json_loads(raw_output)

    except json.JSONDecodeError as e:
        error_result = {
            "session_id": effective_session_id,
            "intent": "parse_error",
            "commands": [],
            "clarification_needed": True,
            "clarification_turn": 1,
            "clarification_question": "명령을 해석하지 못했습니다. 다시 말씀해 주세요.",
            "pending_command": {
                "raw_text": raw_text,
                "llm_raw_output": raw_output,
                "error": str(e),
            },
            "response_text": "명령을 해석하지 못했습니다. 다시 말씀해 주세요.",
        }

        save_parse_session(
            db=db,
            session_id=effective_session_id,
            intent=error_result["intent"],
            clarification_needed=error_result["clarification_needed"],
            pending_command=error_result["pending_command"],
            clarification_turn=error_result["clarification_turn"],
        )

        return error_result

    # 필수 필드 보정
    parsed["session_id"] = effective_session_id
    parsed.setdefault("intent", "device_control")
    parsed.setdefault("commands", [])
    parsed.setdefault("clarification_needed", False)
    parsed.setdefault(
        "clarification_turn",
        1 if parsed["clarification_needed"] else 0,
    )
    parsed.setdefault("clarification_question", None)
    parsed.setdefault("pending_command", None)
    parsed.setdefault("response_text", "")

    # LLM 결과 검증
    is_valid, error_message = validate_llm_parse_result(
        parsed=parsed,
        tools_data=tools_data,
        states_data=states_data,
    )

    if not is_valid:
        validation_result = {
            "session_id": effective_session_id,
            "intent": "validation_error",
            "commands": [],
            "clarification_needed": True,
            "clarification_turn": 1,
            "clarification_question": "명령 형식이 올바르지 않습니다. 다시 말씀해 주세요.",
            "pending_command": {
                "raw_text": raw_text,
                "validation_error": error_message,
                "llm_result": parsed,
            },
            "response_text": "명령 형식이 올바르지 않습니다. 다시 말씀해 주세요.",
        }

        save_parse_session(
            db=db,
            session_id=effective_session_id,
            intent=validation_result["intent"],
            clarification_needed=validation_result["clarification_needed"],
            pending_command=validation_result["pending_command"],
            clarification_turn=validation_result["clarification_turn"],
        )

        return validation_result

    # 정상 결과 세션 저장
    save_parse_session(
        db=db,
        session_id=effective_session_id,
        intent=parsed["intent"],
        clarification_needed=parsed["clarification_needed"],
        pending_command=parsed["pending_command"],
        clarification_turn=parsed["clarification_turn"],
    )

    return parsed