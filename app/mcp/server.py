"""
FastMCP 서버: 스마트홈 기기 제어 Tools, Resources, Prompts 정의
"""
import json
from typing import Optional, List, Union
from fastmcp import FastMCP
from app.core.state_manager import device_states, apply_device_control, broadcast_state
import asyncio

mcp = FastMCP("SmartHome AIoT")

# ─── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def control_air_conditioner(
    power: Optional[str] = None,
    temperature: Optional[int] = None,
    mode: Optional[str] = None,
    fan_speed: Optional[str] = None,
    louver_angle: Optional[str] = None,
) -> str:
    """에어컨을 제어합니다."""
    params = {
        "power": power,
        "temperature": temperature,
        "mode": mode,
        "fan_speed": fan_speed,
        "louver_angle": louver_angle,
    }
    changed = apply_device_control("air_conditioner", params)
    await broadcast_state()
    return json.dumps({"status": "ok", "device": "air_conditioner", "changed": changed})

@mcp.tool()
async def control_tv(
    power: Optional[str] = None,
    channel: Optional[str] = None,
    content_name: Optional[str] = None,
) -> str:
    """TV를 제어합니다."""
    params = {"power": power, "channel": channel, "content_name": content_name}
    changed = apply_device_control("tv", params)
    await broadcast_state()
    return json.dumps({"status": "ok", "device": "tv", "changed": changed})

@mcp.tool()
async def control_air_purifier(
    power: Optional[str] = None,
    mode: Optional[str] = None,
) -> str:
    """공기청정기를 제어합니다."""
    params = {"power": power, "mode": mode}
    changed = apply_device_control("air_purifier", params)
    await broadcast_state()
    return json.dumps({"status": "ok", "device": "air_purifier", "changed": changed})

@mcp.tool()
async def control_robot_vacuum(
    action: Optional[str] = None,
    zone: Optional[Union[str, List[str]]] = None,
    suction_power: Optional[str] = None,
    cleaning_mode: Optional[str] = None,
) -> str:
    """로봇청소기를 제어합니다."""
    params = {
        "action": action,
        "zone": zone,
        "suction_power": suction_power,
        "cleaning_mode": cleaning_mode,
    }
    # action이 있으면 상태 동기화
    if action == "start_cleaning":
        params["action"] = "cleaning"
    elif action == "return_to_dock":
        params["action"] = "returning"
    changed = apply_device_control("robot_vacuum", params)
    await broadcast_state()
    return json.dumps({"status": "ok", "device": "robot_vacuum", "changed": changed})

# ─── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("devices://state")
def get_devices_state() -> str:
    """현재 전체 기기 상태 반환"""
    return json.dumps(device_states.model_dump(), ensure_ascii=False)

# ─── Prompts ──────────────────────────────────────────────────────────────────

CLARIFICATION_PROMPTS = {
    "hot": "에어컨을 켤까요? 몇 도로 맞춰드릴까요?",
    "humid": "에어컨 제습 모드로 켤까요, 제습기를 작동할까요?",
    "dirty_home": "전체 청소할까요, 특정 방만 청소할까요?",
    "sleepy": "수면 모드로 설정할까요? 에어컨 끄고 TV도 끌게요?",
    "guest_arrival": "손님맞이 준비할까요? 에어컨이랑 청소기 같이 돌릴게요?",
    "air_quality": "공기청정기 켤까요? 강하게 할까요?",
    "unknown_content": "어떤 채널이나 콘텐츠를 원하세요? (Netflix, KBS, MBC 등)",
    "outing": "외출 모드로 설정할까요? 전체 기기 끄고 청소기 돌릴게요?",
}

@mcp.prompt()
def clarification_prompt(context_trigger: str) -> str:
    """상황별 재질문 템플릿 반환"""
    return CLARIFICATION_PROMPTS.get(context_trigger, "좀 더 구체적으로 말씀해 주시겠어요?")