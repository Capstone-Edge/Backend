from typing import Optional, List, Union
from pydantic import BaseModel
import asyncio

# --- 기존 기기 상태 모델 ---

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
    mode: str = "auto"  # auto, manual, sleep
    fan_speed: str = "low"
    air_quality: str = "good"
    pm25: int = 15
    filter_status: str = "clean"

class Position(BaseModel):
    x: float = 0.0
    y: float = 0.0

class RobotVacuumState(BaseModel):
    status: str = "docked"  # idle, cleaning, paused, returning, docked, error
    battery_pct: int = 100
    zone: Optional[Union[str, List[str]]] = None
    suction_power: str = "standard"  # quiet, standard, strong, max
    cleaning_mode: str = "auto"  # auto, zigzag, spot, edge
    cleaned_area_m2: float = 0.0
    position: Position = Position()
    do_not_disturb: bool = False
    error: Optional[str] = None


# --- 새로 추가된 기기 상태 모델 ---

class OvenState(BaseModel):
    power: str = "off"
    mode: str = "bake"
    target_temp: int = 180
    current_temp: int = 25
    timer_remaining: int = 0
    fan_speed: str = "off"
    steam: str = "off"
    probe_temp: int = 25
    light: str = "off"
    door: str = "closed"

class WashingMachineState(BaseModel):
    power: str = "off"
    mode: str = "standard"
    status: str = "stopped"
    remaining_time: int = 0
    spin_speed: str = "medium"
    door: str = "closed"
    water_temperature: int = 30
    reservation_time: Optional[str] = None
    error: Optional[str] = None


# --- 전역 상태 묶음 ---

class DeviceStates(BaseModel):
    air_conditioner: AirConditionerState = AirConditionerState()
    tv: TVState = TVState()
    air_purifier: AirPurifierState = AirPurifierState()
    robot_vacuum: RobotVacuumState = RobotVacuumState()
    # 새로 추가된 기기 연결
    oven: OvenState = OvenState()
    washing_machine: WashingMachineState = WashingMachineState()

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
    
    # getattr를 활용해 if/elif 반복 없이 깔끔하게 상태 객체를 가져옵니다
    state = getattr(device_states, device, None)
    
    if state:
        for key, val in params.items():
            # 상태 객체에 해당 파라미터가 존재하고 값이 null이 아닐 경우에만 업데이트
            if val is not None and hasattr(state, key):
                setattr(state, key, val)
                changed[key] = val
                
    return changed