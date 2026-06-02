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

    # === 새로 추가된 기기들의 재질문 처리 ===

    # 3. 오븐 동작/온도 재질문 처리
    if device_type == "oven" and "action_or_parameter" in missing_parameters:
        commands = []
        response_text = ""

        if "켜" in user_answer:
            commands.append({
                "step_order": 1, "device_name": device_name or "kitchen_oven",
                "device_type": "oven", "tool_name": "oven.set_power", "parameters": {"power": "on"}
            })
            response_text = "주방 오븐을 켤게요."
        elif "꺼" in user_answer:
            commands.append({
                "step_order": 1, "device_name": device_name or "kitchen_oven",
                "device_type": "oven", "tool_name": "oven.set_power", "parameters": {"power": "off"}
            })
            response_text = "주방 오븐을 끌게요."
        else:
            match = re.search(r"(\d{2,3})\s*도", user_answer)
            if match:
                temperature = int(match.group(1))
                commands.append({
                    "step_order": 1, "device_name": device_name or "kitchen_oven",
                    "device_type": "oven", "tool_name": "oven.set_temperature", "parameters": {"target_temp": temperature}
                })
                response_text = f"오븐 온도를 {temperature}도로 설정할게요."

        if not commands:
            return {
                "session_id": session_id, "intent": "device_control", "commands": [],
                "clarification_needed": True, "clarification_turn": 2,
                "clarification_question": "전원이나 설정할 온도를 말씀해 주세요.",
                "pending_command": pending, "response_text": "전원이나 설정할 온도를 말씀해 주세요."
            }

        return {
            "session_id": session_id, "intent": "device_control", "commands": commands,
            "clarification_needed": False, "clarification_turn": 1,
            "clarification_question": None, "pending_command": None, "response_text": response_text,
        }

    # 4. 공기청정기 동작 재질문 처리
    if device_type == "air_purifier" and "action_or_parameter" in missing_parameters:
        commands = []
        response_text = ""

        if "켜" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "living_room_air_purifier", "device_type": "air_purifier", "tool_name": "air_purifier.set_power", "parameters": {"power": "on"}})
            response_text = "거실 공기청정기를 켤게요."
        elif "꺼" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "living_room_air_purifier", "device_type": "air_purifier", "tool_name": "air_purifier.set_power", "parameters": {"power": "off"}})
            response_text = "거실 공기청정기를 끌게요."

        if not commands:
            return {
                "session_id": session_id, "intent": "device_control", "commands": [],
                "clarification_needed": True, "clarification_turn": 2,
                "clarification_question": "켜드릴까요, 꺼드릴까요?",
                "pending_command": pending, "response_text": "켜드릴까요, 꺼드릴까요?"
            }

        return {
            "session_id": session_id, "intent": "device_control", "commands": commands,
            "clarification_needed": False, "clarification_turn": 1, "clarification_question": None, "pending_command": None, "response_text": response_text,
        }

    # 5. 세탁기 동작 재질문 처리
    if device_type == "washing_machine" and "action_or_parameter" in missing_parameters:
        commands = []
        response_text = ""

        if "켜" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "utility_room_washing_machine", "device_type": "washing_machine", "tool_name": "washing_machine.set_power", "parameters": {"power": "on"}})
            response_text = "다용도실 세탁기를 켤게요."
        elif "돌려" in user_answer or "시작" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "utility_room_washing_machine", "device_type": "washing_machine", "tool_name": "washing_machine.set_action", "parameters": {"action": "start"}})
            response_text = "세탁을 시작할게요."

        if not commands:
            return {
                "session_id": session_id, "intent": "device_control", "commands": [],
                "clarification_needed": True, "clarification_turn": 2,
                "clarification_question": "세탁기를 켤까요, 아니면 바로 세탁을 시작할까요?",
                "pending_command": pending, "response_text": "세탁기를 켤까요, 아니면 바로 세탁을 시작할까요?"
            }

        return {
            "session_id": session_id, "intent": "device_control", "commands": commands,
            "clarification_needed": False, "clarification_turn": 1, "clarification_question": None, "pending_command": None, "response_text": response_text,
        }

    # 6. 로봇청소기 동작 재질문 처리
    if device_type == "robot_vacuum" and "action_or_parameter" in missing_parameters:
        commands = []
        response_text = ""

        if "돌려" in user_answer or "시작" in user_answer or "청소" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "living_room_robot_vacuum", "device_type": "robot_vacuum", "tool_name": "robot_vacuum.set_action", "parameters": {"action": "start_cleaning"}})
            response_text = "로봇청소기 청소를 시작할게요."
        elif "멈춰" in user_answer or "정지" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "living_room_robot_vacuum", "device_type": "robot_vacuum", "tool_name": "robot_vacuum.set_action", "parameters": {"action": "pause"}})
            response_text = "로봇청소기를 일시정지할게요."
        elif "충전" in user_answer or "돌아가" in user_answer:
            commands.append({"step_order": 1, "device_name": device_name or "living_room_robot_vacuum", "device_type": "robot_vacuum", "tool_name": "robot_vacuum.set_action", "parameters": {"action": "return_to_dock"}})
            response_text = "로봇청소기를 충전기로 돌려보낼게요."

        if not commands:
            return {
                "session_id": session_id, "intent": "device_control", "commands": [],
                "clarification_needed": True, "clarification_turn": 2,
                "clarification_question": "청소를 시작할까요, 일시정지할까요, 충전기로 돌려보낼까요?",
                "pending_command": pending, "response_text": "청소를 시작할까요, 일시정지할까요, 충전기로 돌려보낼까요?"
            }

        return {
            "session_id": session_id, "intent": "device_control", "commands": commands,
            "clarification_needed": False, "clarification_turn": 1, "clarification_question": None, "pending_command": None, "response_text": response_text,
        }

    # 매칭되는 조건이 없을 경우 기본 폴백 응답
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
