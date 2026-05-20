from typing import Optional, List, Union
from pydantic import BaseModel
import asyncio

class AirConditionerState(BaseModel):
    power: str = "off"
    temperature: int = 24
    mode: str = "cool"  # cool, heat, dry, fan
    fan_speed: str = "auto"  # auto, low, medium, high
    louver_angle: str = "mid"  # up, mid, down, swing

class TVState(BaseModel):
    power: str = "off"
    channel: Optional[str] = None
    content_name: Optional[str] = None

class AirPurifierState(BaseModel):
    power: str = "off"
    mode: str = "auto"  # auto, quiet, standard, strong, turbo

class RobotVacuumState(BaseModel):
    action: str = "idle"  # idle, cleaning, paused, returning, docked
    zone: Optional[Union[str, List[str]]] = None
    suction_power: str = "standard"  # quiet, standard, strong, max
    cleaning_mode: str = "auto"  # auto, zigzag, spot, edge

class DeviceStates(BaseModel):
    air_conditioner: AirConditionerState = AirConditionerState()
    tv: TVState = TVState()
    air_purifier: AirPurifierState = AirPurifierState()
    robot_vacuum: RobotVacuumState = RobotVacuumState()

# 전역 상태 싱글톤
device_states = DeviceStates()

# WebSocket 연결 목록
websocket_connections: List = []

async def broadcast_state():
    """모든 WebSocket 클라이언트에 현재 상태 브로드캐스트"""
    import json
    state_json = json.dumps(device_states.model_dump())
    dead = []
    for ws in websocket_connections:
        try:
            await ws.send_text(state_json)
        except Exception:
            dead.append(ws)
    for ws in dead:
        websocket_connections.remove(ws)

def apply_device_control(device: str, params: dict) -> dict:
    """기기 상태 업데이트 및 변경된 필드 반환"""
    changed = {}
    if device == "air_conditioner":
        state = device_states.air_conditioner
        for key, val in params.items():
            if val is not None and hasattr(state, key):
                setattr(state, key, val)
                changed[key] = val
    elif device == "tv":
        state = device_states.tv
        for key, val in params.items():
            if val is not None and hasattr(state, key):
                setattr(state, key, val)
                changed[key] = val
    elif device == "air_purifier":
        state = device_states.air_purifier
        for key, val in params.items():
            if val is not None and hasattr(state, key):
                setattr(state, key, val)
                changed[key] = val
    elif device == "robot_vacuum":
        state = device_states.robot_vacuum
        for key, val in params.items():
            if val is not None and hasattr(state, key):
                setattr(state, key, val)
                changed[key] = val
    return changed
