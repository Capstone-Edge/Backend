import re
import json
from sqlalchemy import text

from app.api.v1.mcp import get_mcp_tools, get_mcp_device_states
from app.api.v1.routines import get_routines, get_routine_detail


async def parse_natural_language(
    raw_text: str,
    session_id: str | None = None,
    device_id: str | None = None,
    source: str | None = "edge",
    db=None,
):
    raw_text = raw_text.strip()

    # Backend 내부 함수로 Tool/State/Routine 조회
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


    commands = []
    clarification_needed = False
    clarification_question = None
    pending_command = None
    intent = "device_control"
    response_text = ""

    # 1. TV 콘텐츠 재생
    if "틀어" in raw_text or "재생" in raw_text:
        content_title = (
            raw_text
            .replace("틀어줘", "")
            .replace("틀어", "")
            .replace("재생해줘", "")
            .replace("재생", "")
            .replace("TV", "")
            .replace("티비", "")
            .strip()
        )

        app_name = None

        if "유튜브" in raw_text:
            app_name = "youtube"
            content_title = content_title.replace("유튜브에서", "").replace("유튜브", "").strip()
        elif "넷플릭스" in raw_text:
            app_name = "netflix"
            content_title = content_title.replace("넷플릭스에서", "").replace("넷플릭스", "").strip()

        if not content_title:
            clarification_needed = True
            clarification_question = "어떤 콘텐츠를 재생할까요?"
            pending_command = {
                "device_name": "living_room_tv",
                "device_type": "tv",
                "candidate_tools": ["tv.set_power", "tv.play_content"],
                "missing_parameters": ["content_title"],
            }
            response_text = clarification_question
            commands = []
        else:
            commands = [
                {
                    "step_order": 1,
                    "device_name": "living_room_tv",
                    "device_type": "tv",
                    "tool_name": "tv.set_power",
                    "parameters": {"power": "on"},
                },
                {
                    "step_order": 2,
                    "device_name": "living_room_tv",
                    "device_type": "tv",
                    "tool_name": "tv.play_content",
                    "parameters": {"content_title": content_title},
                },
            ]

            if app_name:
                commands[1]["parameters"]["app_name"] = app_name
                response_text = f"TV를 켜고 {app_name}에서 {content_title}를 재생할게요."
            else:
                response_text = f"TV를 켜고 {content_title}를 재생할게요."

    # 2. 에어컨 명시 제어
    elif "에어컨" in raw_text:
        if "켜" in raw_text:
            commands.append({
                "step_order": 1,
                "device_name": "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_power",
                "parameters": {"power": "on"},
            })
            response_text = "거실 에어컨을 켤게요."

        if "꺼" in raw_text:
            commands.append({
                "step_order": len(commands) + 1,
                "device_name": "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_power",
                "parameters": {"power": "off"},
            })
            response_text = "거실 에어컨을 끌게요."

        match = re.search(r"(\d{2})\s*도", raw_text)
        if match:
            temperature = int(match.group(1))
            commands.append({
                "step_order": len(commands) + 1,
                "device_name": "living_room_aircon",
                "device_type": "air_conditioner",
                "tool_name": "air_conditioner.set_temperature",
                "parameters": {"temperature": temperature},
            })
            response_text = f"거실 에어컨을 {temperature}도로 설정할게요."

        if not commands:
            clarification_needed = True
            clarification_question = "에어컨을 어떻게 설정할까요? 전원, 온도, 모드 중 원하는 내용을 말씀해 주세요."
            pending_command = {
                "device_name": "living_room_aircon",
                "device_type": "air_conditioner",
                "candidate_tools": [
                    "air_conditioner.set_power",
                    "air_conditioner.set_temperature",
                    "air_conditioner.set_mode",
                ],
                "missing_parameters": ["action_or_parameter"],
            }
            response_text = clarification_question

    # 3. 조명 제어
    elif "불" in raw_text or "조명" in raw_text:
        if "켜" in raw_text:
            commands.append({
                "step_order": 1,
                "device_name": "living_room_light",
                "device_type": "light",
                "tool_name": "light.set_power",
                "parameters": {"power": "on"},
            })
            response_text = "거실 조명을 켤게요."

        if "꺼" in raw_text:
            commands.append({
                "step_order": len(commands) + 1,
                "device_name": "living_room_light",
                "device_type": "light",
                "tool_name": "light.set_power",
                "parameters": {"power": "off"},
            })
            response_text = "거실 조명을 끌게요."

        match = re.search(r"(\d{1,3})\s*퍼", raw_text)
        if match:
            brightness = int(match.group(1))
            commands.append({
                "step_order": len(commands) + 1,
                "device_name": "living_room_light",
                "device_type": "light",
                "tool_name": "light.set_brightness",
                "parameters": {"brightness": brightness},
            })
            response_text = f"거실 조명 밝기를 {brightness}%로 설정할게요."

        if "영화" in raw_text:
            commands.append({
                "step_order": len(commands) + 1,
                "device_name": "living_room_light",
                "device_type": "light",
                "tool_name": "light.set_scene",
                "parameters": {"scene_name": "movie"},
            })
            response_text = "거실 조명을 영화 모드로 설정할게요."

        if not commands:
            clarification_needed = True
            clarification_question = "조명을 어떻게 조절할까요? 전원, 밝기, 색상, 장면 모드 중 선택해 주세요."
            pending_command = {
                "device_name": "living_room_light",
                "device_type": "light",
                "candidate_tools": [
                    "light.set_power",
                    "light.set_brightness",
                    "light.set_color",
                    "light.set_scene",
                ],
                "missing_parameters": ["action_or_parameter"],
            }
            response_text = clarification_question

    # 4. 모호한 더움 표현
    elif "덥" in raw_text or "더워" in raw_text:
        clarification_needed = True
        clarification_question = "에어컨을 몇 도로 맞춰드릴까요?"
        pending_command = {
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
        }
        response_text = clarification_question

    # 5. 루틴 호출
    elif "수면 모드" in raw_text:
        intent = "routine_control"
        routine = get_routine_detail("sleep", db=db)
        commands = routine["steps"]
        response_text = "수면 모드로 설정할게요."

    elif "외출 모드" in raw_text:
        intent = "routine_control"
        routine = get_routine_detail("away", db=db)
        commands = routine["steps"]
        response_text = "외출 모드로 설정할게요."

    elif "영화 모드" in raw_text:
        intent = "routine_control"
        routine = get_routine_detail("movie", db=db)
        commands = routine["steps"]
        response_text = "영화 모드로 설정할게요."

    else:
        clarification_needed = True
        clarification_question = "어떤 기기를 어떻게 제어할까요?"
        pending_command = {
            "raw_text": raw_text,
            "missing_parameters": ["device", "action"],
        }
        response_text = clarification_question



    effective_session_id = session_id or "mock-session-001"

    if db is not None:
        existing_session = db.execute(
            text("""
                SELECT id
                FROM dialogue_sessions
                WHERE session_id = :session_id
                LIMIT 1
            """),
            {"session_id": effective_session_id},
        ).mappings().first()

        if clarification_needed:
            pending_command_json = json.dumps(pending_command or {}, ensure_ascii=False)

            if existing_session:
                db.execute(
                    text("""
                        UPDATE dialogue_sessions
                        SET status = :status,
                            pending_command = :pending_command,
                            clarification_turn = :clarification_turn,
                            last_intent = :last_intent,
                            updated_at = NOW()
                        WHERE session_id = :session_id
                    """),
                    {
                        "session_id": effective_session_id,
                        "status": "pending",
                        "pending_command": pending_command_json,
                        "clarification_turn": 1,
                        "last_intent": intent,
                    },
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO dialogue_sessions (
                            session_id,
                            messages,
                            status,
                            pending_command,
                            clarification_turn,
                            last_intent,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :session_id,
                            :messages,
                            :status,
                            :pending_command,
                            :clarification_turn,
                            :last_intent,
                            NOW(),
                            NOW()
                        )
                    """),
                    {
                        "session_id": effective_session_id,
                        "messages": json.dumps([], ensure_ascii=False),
                        "status": "pending",
                        "pending_command": pending_command_json,
                        "clarification_turn": 1,
                        "last_intent": intent,
                    },
                )
        else:
            if existing_session:
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
                        "session_id": effective_session_id,
                        "status": "active",
                        "last_intent": intent,
                    },
                )
            else:
                db.execute(
                    text("""
                        INSERT INTO dialogue_sessions (
                            session_id,
                            messages,
                            status,
                            pending_command,
                            clarification_turn,
                            last_intent,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :session_id,
                            :messages,
                            :status,
                            NULL,
                            0,
                            :last_intent,
                            NOW(),
                            NOW()
                        )
                    """),
                    {
                        "session_id": effective_session_id,
                        "messages": json.dumps([], ensure_ascii=False),
                        "status": "active",
                        "last_intent": intent,
                    },
                )

        db.commit()


    return {
        "session_id": effective_session_id,
        "intent": intent,
        "commands": commands,
        "clarification_needed": clarification_needed,
        "clarification_turn": 1 if clarification_needed else 0,
        "clarification_question": clarification_question,
        "pending_command": pending_command,
        "response_text": response_text,
        "debug": {
            "tools_count": len(tools_data.get("tools", [])),
            "device_states_count": len(states_data.get("devices", [])),
            "routines_count": len(routines_data.get("routines", [])),
        },
    }