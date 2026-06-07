import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.ws_manager import ws_manager

router = APIRouter(prefix="/api/v1/commands", tags=["Commands"])


class CommandItem(BaseModel):
    step_order: int
    device_name: str
    device_type: str
    tool_name: str
    parameters: dict[str, Any]


class ExecuteCommandRequest(BaseModel):
    session_id: str
    raw_user_input: str | None = None
    intent: str
    commands: list[CommandItem]
    response_text: str


def normalize_state_data(state_data):
    if isinstance(state_data, str):
        return json.loads(state_data)
    return state_data or {}


def apply_command_to_state(state: dict[str, Any], tool_name: str, parameters: dict[str, Any]):
    """
    MVP 기준 상태 업데이트 로직.
    tool_name별로 parameters 값을 device_states.state_data에 반영한다.
    """

    # 공통 전원
    if tool_name.endswith(".set_power"):
        state["power"] = parameters["power"]
        if tool_name == "tv.set_power" and parameters["power"] == "on":
            state["volume"] = 10

    # 에어컨
    elif tool_name == "air_conditioner.set_temperature":
        temp = int(parameters["temperature"])
        if not (18 <= temp <= 30):
            raise ValueError(f"에어컨 온도는 18~30°C 범위만 가능합니다. (요청값: {temp}°C)")
        state["temperature"] = temp
    elif tool_name == "air_conditioner.set_mode":
        state["mode"] = parameters["mode"]
    elif tool_name == "air_conditioner.set_fan_speed":
        state["fan_speed"] = parameters["fan_speed"]
    elif tool_name == "air_conditioner.set_louver_angle":
        state["louver_angle"] = parameters["louver_angle"]
    elif tool_name == "air_conditioner.set_timer":
        state["timer"] = {
            "delay_minutes": parameters["delay_minutes"]
        }

    # 조명
    elif tool_name == "light.set_brightness":
        state["brightness"] = parameters["brightness"]
    elif tool_name == "light.set_color":
        state["color"] = parameters["color"]
    elif tool_name == "light.set_color_temperature":
        state["color_temperature"] = parameters["color_temperature"]
    elif tool_name == "light.set_scene":
        state["scene_name"] = parameters["scene_name"]

    # TV
    elif tool_name == "tv.set_volume":
        state["volume"] = parameters["volume"]
    elif tool_name == "tv.set_volume":
        state["volume"] = parameters["volume"]
    elif tool_name == "tv.set_channel":
        state["power"] = "on"
        state["channel"] = str(parameters["channel"])
        state["content_name"] = None
    elif tool_name == "tv.open_app":
        state["power"] = "on"
        state["app_name"] = parameters["app_name"]
        state["content_name"] = parameters["app_name"]
    elif tool_name == "tv.play_content":
        state["power"] = "on"
        state["content_name"] = parameters["content_title"]
        if "app_name" in parameters:
            state["app_name"] = parameters["app_name"]

    # 오븐
    elif tool_name == "oven.set_temperature":
        state["target_temp"] = parameters["target_temp"]
    elif tool_name == "oven.set_mode":
        state["mode"] = parameters["mode"]
    elif tool_name == "oven.set_fan_speed":
        state["fan_speed"] = parameters["fan_speed"]
    elif tool_name == "oven.set_steam":
        state["steam"] = parameters["steam"]
    elif tool_name == "oven.set_probe_target":
        state["probe_temp"] = parameters["probe_target"]

    # 공기청정기
    elif tool_name == "air_purifier.set_mode":
        state["mode"] = parameters["mode"]
    elif tool_name == "air_purifier.set_fan_speed":
        state["fan_speed"] = parameters["fan_speed"]

    # 세탁기
    elif tool_name == "washing_machine.set_action":
        _wm_action_to_status = {
            "start":   "washing",
            "stop":    "stopped",
            "pause":   "stopped",
            "resume":  "washing",
        }
        state["status"] = _wm_action_to_status.get(parameters["action"], parameters["action"])
    elif tool_name == "washing_machine.set_mode":
        state["mode"] = parameters["mode"]
    elif tool_name == "washing_machine.set_spin_speed":
        state["spin_speed"] = parameters["spin_speed"]
    elif tool_name == "washing_machine.set_water_temperature":
        state["water_temperature"] = parameters["water_temperature"]
    elif tool_name == "washing_machine.set_reservation":
        state["reservation_time"] = parameters["start_time"]

    # 로봇청소기
    elif tool_name == "robot_vacuum.set_action":
        _action_to_status = {
            "start_cleaning": "cleaning",
            "pause": "paused",
            "return_to_dock": "returning",
        }
        state["status"] = _action_to_status.get(parameters["action"], parameters["action"])
    elif tool_name == "robot_vacuum.set_zone":
        state["zone"] = parameters["zone"]
    elif tool_name == "robot_vacuum.set_suction_power":
        state["suction_power"] = parameters["suction_power"]
    elif tool_name == "robot_vacuum.set_cleaning_mode":
        state["cleaning_mode"] = parameters["cleaning_mode"]

    else:
        raise ValueError(f"Unsupported tool_name: {tool_name}")

    return state


@router.post("/execute")
async def execute_commands(
    request: ExecuteCommandRequest,
    db: Session = Depends(get_db),
):
    if not request.commands:
        raise HTTPException(status_code=400, detail="commands must not be empty")

    executed_commands = []
    updated_states_map = {}

    try:
        session_query = """
            SELECT id
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
        """

        existing_session = db.execute(
            text(session_query),
            {"session_id": request.session_id}
        ).mappings().first()

        if not existing_session:
            create_session_query = """
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
            """

            db.execute(
                text(create_session_query),
                {
                    "session_id": request.session_id,
                    "messages": json.dumps([], ensure_ascii=False),
                    "status": "active",
                    "pending_command": None,
                    "clarification_turn": 0,
                    "last_intent": request.intent,
                }
            )

        for command in sorted(request.commands, key=lambda x: x.step_order):
            # 1. device + command 존재 여부 확인
            lookup_query = """
                SELECT
                    d.id AS device_id,
                    d.name AS device_name,
                    d.display_name AS display_name,
                    d.location AS location,
                    dt.name AS device_type,
                    c.id AS command_id,
                    c.tool_name AS tool_name,
                    ds.state_data AS state_data
                FROM devices d
                JOIN device_types dt ON d.device_type_id = dt.id
                JOIN commands c ON c.device_type_id = dt.id
                JOIN device_states ds ON ds.device_id = d.id
                WHERE d.name = :device_name
                  AND dt.name = :device_type
                  AND c.tool_name = :tool_name
                  AND d.is_active = true
                  AND c.is_active = true
                LIMIT 1
            """

            row = db.execute(
                text(lookup_query),
                {
                    "device_name": command.device_name,
                    "device_type": command.device_type,
                    "tool_name": command.tool_name,
                },
            ).mappings().first()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Invalid device or command: {command.device_name}, {command.tool_name}",
                )

            # 2. 현재 상태 로드
            state = normalize_state_data(row["state_data"])

            # 3. 상태 업데이트
            new_state = apply_command_to_state(
                state=state,
                tool_name=command.tool_name,
                parameters=command.parameters,
            )

            # 4. device_states 업데이트
            update_query = """
                UPDATE device_states
                SET state_data = :state_data,
                    updated_at = NOW()
                WHERE device_id = :device_id
            """

            db.execute(
                text(update_query),
                {
                    "state_data": json.dumps(new_state, ensure_ascii=False),
                    "device_id": row["device_id"],
                },
            )

            # 5. command_logs 저장
            log_query = """
                INSERT INTO command_logs (
                    session_id,
                    device_id,
                    command_id,
                    raw_user_input,
                    input_params,
                    parsed_command,
                    result,
                    status,
                    error_message,
                    executed_at
                )
                VALUES (
                    :session_id,
                    :device_id,
                    :command_id,
                    :raw_user_input,
                    :input_params,
                    :parsed_command,
                    :result,
                    :status,
                    :error_message,
                    NOW()
                )
            """

            db.execute(
                text(log_query),
                {
                    "session_id": request.session_id,
                    "device_id": row["device_id"],
                    "command_id": row["command_id"],
                    "raw_user_input": request.raw_user_input,
                    "input_params": json.dumps(command.parameters, ensure_ascii=False),
                    "parsed_command": json.dumps(command.model_dump(), ensure_ascii=False),
                    "result": json.dumps({"updated_state": new_state}, ensure_ascii=False),
                    "status": "success",
                    "error_message": None,
                },
            )

            executed_commands.append(
                {
                    "step_order": command.step_order,
                    "device_name": command.device_name,
                    "tool_name": command.tool_name,
                    "status": "success",
                }
            )

            updated_states_map[command.device_name] = {
                "device_name": command.device_name,
                "device_type": row["device_type"],
                "display_name": row["display_name"],
                "location": row["location"],
                "state": new_state,
            }

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    updated_states = list(updated_states_map.values())

    # in-memory 상태 동기화 후 /ws 로 전체 상태 브로드캐스트
    from app.core.state_manager import device_states, broadcast_state
    for updated_state in updated_states:
        state_obj = getattr(device_states, updated_state["device_type"], None)
        if state_obj:
            for key, val in updated_state["state"].items():
                if val is not None and hasattr(state_obj, key):
                    setattr(state_obj, key, val)
    await broadcast_state()

    response = {
        "success": True,
        "executed_commands": executed_commands,
        "updated_states": updated_states,
        "response_text": request.response_text,
    }

    for updated_state in updated_states:
        websocket_message = {
            "type": "device_state_update",
            "device_name": updated_state["device_name"],
            "device_type": updated_state["device_type"],
            "display_name": updated_state.get("display_name"),
            "location": updated_state["location"],
            "state": updated_state["state"],
            "source": "ai_command",
            "response_text": request.response_text,
        }

        await ws_manager.broadcast(websocket_message)

    return response
