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

_ZONE_KEYWORDS: dict[str, str] = {
    "거실": "living_room",
    "주방": "kitchen",
    "부엌": "kitchen",
    "침실1": "bedroom1",
    "침실 1": "bedroom1",
    "침실2": "bedroom2",
    "침실 2": "bedroom2",
    "침실3": "bedroom3",
    "침실 3": "bedroom3",
    "세탁실": "laundry",
    "전체": "all",
    "집 전체": "all",
    "모든 방": "all",
}
_CLEAN_KEYWORDS = ["청소", "돌려", "청소해", "쓸어", "닦아"]
_VACUUM_GENERAL_KEYWORDS = ["청소기", "청소해", "청소 좀", "청소하", "더럽", "지저분"]

# 청소 이외의 다른 기기 키워드 — 복합 명령이면 LLM에 위임
_OTHER_DEVICE_KEYWORDS = [
    "tv", "TV", "티비", "텔레비전",
    "에어컨", "공기청정기", "조명", "오븐", "세탁기",
]

def _has_other_device(raw_text: str) -> bool:
    return any(k in raw_text for k in _OTHER_DEVICE_KEYWORDS)

_ZONE_DISPLAY: dict[str, str] = {
    "living_room": "거실",
    "kitchen": "주방",
    "bedroom1": "침실1",
    "bedroom2": "침실2",
    "bedroom3": "침실3",
    "laundry": "세탁실",
    "all": "집 전체",
}


def _detect_vacuum_zones(raw_text: str) -> list[str]:
    seen: set[str] = set()
    zones: list[str] = []
    for kor, eng in _ZONE_KEYWORDS.items():
        if kor in raw_text and eng not in seen:
            seen.add(eng)
            zones.append(eng)
    return zones


def _detect_vacuum_zone(raw_text: str) -> str | None:
    zones = _detect_vacuum_zones(raw_text)
    return zones[0] if zones else None


def _is_vacuum_zone_request(raw_text: str) -> bool:
    has_clean = any(k in raw_text for k in _CLEAN_KEYWORDS)
    has_zone = bool(_detect_vacuum_zones(raw_text))
    return has_clean and has_zone


def _is_vacuum_no_zone_request(raw_text: str) -> bool:
    """구역 없이 청소를 요청하는 경우 → 재질문 필요"""
    has_vacuum = any(k in raw_text for k in _VACUUM_GENERAL_KEYWORDS)
    has_zone = bool(_detect_vacuum_zones(raw_text))
    return has_vacuum and not has_zone


def _build_vacuum_clarification_result(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "intent": "device_control",
        "commands": [],
        "clarification_needed": True,
        "clarification_turn": 1,
        "clarification_question": "어디를 청소할까요? (예: 거실, 주방, 침실, 전체)",
        "pending_command": {
            "device_name": "living_room_robot_vacuum",
            "device_type": "robot_vacuum",
            "inferred_intent": "vacuum_cleaning",
            "context_trigger": "vacuum_no_zone",
            "candidate_tools": ["robot_vacuum.set_zone", "robot_vacuum.set_action"],
            "known_parameters": {"action": "start_cleaning"},
            "missing_parameters": ["zone"],
        },
        "response_text": "어디를 청소할까요? (예: 거실, 주방, 침실, 전체)",
    }


def _build_vacuum_zone_result(session_id: str, zone: str | list[str]) -> dict[str, Any]:
    if isinstance(zone, list) and len(zone) == 1:
        zone = zone[0]
    if isinstance(zone, list):
        display = " · ".join(_ZONE_DISPLAY.get(z, z) for z in zone)
    else:
        display = _ZONE_DISPLAY.get(zone, zone)
    return {
        "session_id": session_id,
        "intent": "device_control",
        "commands": [
            {
                "step_order": 1,
                "device_name": "living_room_robot_vacuum",
                "device_type": "robot_vacuum",
                "tool_name": "robot_vacuum.set_zone",
                "parameters": {"zone": zone},
            },
            {
                "step_order": 2,
                "device_name": "living_room_robot_vacuum",
                "device_type": "robot_vacuum",
                "tool_name": "robot_vacuum.set_action",
                "parameters": {"action": "start_cleaning"},
            },
        ],
        "clarification_needed": False,
        "clarification_turn": 0,
        "clarification_question": None,
        "pending_command": None,
        "response_text": f"{display} 청소를 시작할게요.",
    }


_AIR_QUALITY_KEYWORDS = ["쾌쾌", "퀴퀴", "냄새", "먼지", "공기 나빠", "공기 탁", "숨막혀", "답답해", "환기"]


def _has_air_quality_issue(raw_text: str) -> bool:
    return any(k in raw_text for k in _AIR_QUALITY_KEYWORDS)


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


def _build_hot_with_air_purifier_result(effective_session_id: str) -> dict[str, Any]:
    return {
        "session_id": effective_session_id,
        "intent": "multi_device_control",
        "commands": [
            {
                "step_order": 1,
                "device_name": "living_room_air_purifier",
                "device_type": "air_purifier",
                "tool_name": "air_purifier.set_power",
                "parameters": {"power": "on"},
            },
            {
                "step_order": 2,
                "device_name": "living_room_air_purifier",
                "device_type": "air_purifier",
                "tool_name": "air_purifier.set_mode",
                "parameters": {"mode": "auto"},
            },
        ],
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
        "response_text": "공기청정기를 켰어요. 에어컨은 몇 도로 맞춰드릴까요?",
    }


async def parse_with_llm(
    raw_text: str,
    session_id: str | None = None,
    device_id: str | None = None,
    source: str | None = "edge",
    db=None,
) -> dict[str, Any]:
    effective_session_id = session_id or "mock-session-001"

    if _is_vacuum_zone_request(raw_text) and not _has_other_device(raw_text):
        zones = _detect_vacuum_zones(raw_text)
        zone: str | list[str] = zones[0] if len(zones) == 1 else zones
        forced_result = _build_vacuum_zone_result(effective_session_id, zone)
        save_parse_session(
            db=db,
            session_id=effective_session_id,
            intent=forced_result["intent"],
            clarification_needed=False,
            pending_command=None,
            clarification_turn=0,
        )
        return forced_result

    if _is_vacuum_no_zone_request(raw_text) and not _has_other_device(raw_text):
        forced_result = _build_vacuum_clarification_result(effective_session_id)
        save_parse_session(
            db=db,
            session_id=effective_session_id,
            intent=forced_result["intent"],
            clarification_needed=True,
            pending_command=forced_result["pending_command"],
            clarification_turn=1,
        )
        return forced_result

    if _is_ambiguous_hot_request(raw_text):
        if _has_air_quality_issue(raw_text):
            forced_result = _build_hot_with_air_purifier_result(effective_session_id)
        else:
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