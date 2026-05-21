import re


async def clarify_natural_language(
    session_id: str,
    user_answer: str,
    pending_command: dict | None = None,
):
    user_answer = user_answer.strip()
    pending = pending_command or {}

    device_type = pending.get("device_type")
    device_name = pending.get("device_name")
    missing_parameters = pending.get("missing_parameters", [])

    # 1. 에어컨 온도 재질문 처리
    if device_type == "air_conditioner" and "temperature" in missing_parameters:
        match = re.search(r"(\d{2})\s*도", user_answer)

        if not match:
            return {
                "session_id": session_id,
                "intent": "device_control",
                "commands": [],
                "clarification_needed": True,
                "clarification_turn": 2,
                "clarification_question": "몇 도로 맞춰드릴까요? 예: 24도",
                "pending_command": pending,
                "response_text": "몇 도로 맞춰드릴까요?",
            }

        temperature = int(match.group(1))

        commands = [
            {
                "step_order": 1,
                "device_name": device_name or "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_power",
                "parameters": {"power": "on"},
            },
            {
                "step_order": 2,
                "device_name": device_name or "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_mode",
                "parameters": {"mode": "cool"},
            },
            {
                "step_order": 3,
                "device_name": device_name or "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_temperature",
                "parameters": {"temperature": temperature},
            },
        ]

        return {
            "session_id": session_id,
            "intent": "device_control",
            "commands": commands,
            "clarification_needed": False,
            "clarification_turn": 1,
            "clarification_question": None,
            "pending_command": None,
            "response_text": f"거실 에어컨을 {temperature}도 냉방으로 켤게요.",
        }

    # 2. TV 콘텐츠명 재질문 처리
    if device_type == "tv" and "content_title" in missing_parameters:
        content_title = user_answer.strip()

        if not content_title:
            return {
                "session_id": session_id,
                "intent": "device_control",
                "commands": [],
                "clarification_needed": True,
                "clarification_turn": 2,
                "clarification_question": "어떤 콘텐츠를 재생할까요?",
                "pending_command": pending,
                "response_text": "어떤 콘텐츠를 재생할까요?",
            }

        commands = [
            {
                "step_order": 1,
                "device_name": device_name or "living_room_tv",
                "device_type": "tv",
                "tool_name": "tv.set_power",
                "parameters": {"power": "on"},
            },
            {
                "step_order": 2,
                "device_name": device_name or "living_room_tv",
                "device_type": "tv",
                "tool_name": "tv.play_content",
                "parameters": {"content_title": content_title},
            },
        ]

        return {
            "session_id": session_id,
            "intent": "device_control",
            "commands": commands,
            "clarification_needed": False,
            "clarification_turn": 1,
            "clarification_question": None,
            "pending_command": None,
            "response_text": f"TV를 켜고 {content_title}를 재생할게요.",
        }

    return {
        "session_id": session_id,
        "intent": "device_control",
        "commands": [],
        "clarification_needed": True,
        "clarification_turn": 2,
        "clarification_question": "조금 더 구체적으로 말씀해 주세요.",
        "pending_command": pending,
        "response_text": "조금 더 구체적으로 말씀해 주세요.",
    }