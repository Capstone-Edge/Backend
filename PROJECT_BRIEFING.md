# Edge Backend — 프로젝트 완전 학습 브리핑

> 다른 Claude AI 인스턴스가 이 프로젝트에 즉시 협업할 수 있도록
> 모든 파일을 직접 읽고 작성한 정확한 학습 자료입니다. (2026-06-13 기준, feat/jimin 브랜치)

---

## 1. 프로젝트 개요

**목적:** 자연어(음성 포함) 명령을 MCP Tool 규격의 JSON commands로 변환해 스마트홈 기기를 제어하는 Edge AI 백엔드.

**핵심 흐름:**
```
사용자 자연어 입력 (raw_text / stt_text)
  → 규칙 숏컷 (4가지) 또는 Claude Haiku LLM 파싱
  → 재질문(clarification) 필요 시 최대 5턴 대화
  → commands 실행 (MySQL DB 저장 + WebSocket 브로드캐스트)
  → 대화 로그 실시간 push (dialogue WebSocket)
```

**브랜치:** `feat/jimin` / 주 브랜치: `main`  
**서버 주소:** `http://localhost:8000`

---

## 2. 기술 스택

| 항목 | 상세 |
|------|------|
| 웹 프레임워크 | FastAPI 0.115.0 (REST + WebSocket) |
| DB | MySQL `smart_home_aiot` (localhost:3306, user: root) |
| ORM | SQLAlchemy + PyMySQL (raw SQL text() 위주로 사용) |
| AI | Anthropic SDK 0.49.0 — 동기: `Anthropic()`, 비동기: `AsyncAnthropic()` |
| 기본 모델 | `claude-haiku-4-5-20251001` (env `ANTHROPIC_MODEL`로 오버라이드) |
| MCP | ~~fastmcp 2.3.4, mcp 1.12.4~~ → 삭제됨 (실제 MCP 서버 미운용, app/mcp/ 폴더 제거) |
| ASGI | uvicorn 0.30.6 |
| 검증 | Pydantic v2 |
| 환경변수 | `PARSER_MODE=llm` (현재 운용값) — `rule`이면 키워드 파서 |

**서버 실행:**
```bash
# .env 파일
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
PARSER_MODE=llm

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. 디렉토리 구조 (전체 파일 설명)

```
app/
├── main.py                    # FastAPI 앱 진입점, 라우터 등록
│                              # legacy /ws WebSocket, /api/v1/command/execute (legacy)
│                              # /api/v1/devices/state (in-memory 상태 반환)
│                              # /ws/device-states WebSocket
├── api/v1/
│   ├── edge.py                # POST /api/v1/commands/parse   — NLU만, 실행 없음
│   │                          # POST /api/v1/dialogues/clarify — 재질문 처리만, 실행 없음
│   ├── mcp.py                 # GET  /api/v1/mcp/resources/device-states
│   │                          # GET  /api/v1/mcp/tools (DB commands 테이블 → MCP Tool 스키마)
│   ├── routines.py            # GET  /api/v1/routines
│   │                          # GET  /api/v1/routines/{routine_name}
│   ├── commands.py            # POST /api/v1/commands/execute ★실행 계층 핵심
│   │                          # apply_command_to_state() — tool_name별 DB state 업데이트
│   │                          # execute_commands() — DB저장, command_logs, WS broadcast
│   ├── command_process.py     # POST /api/v1/commands/process ★메인 통합 파이프라인
│   │                          # POST /api/v1/commands/process-clarify
│   │                          # pending TTL 30초, 취소어 감지, 다른 기기 명령 자동 취소
│   ├── dialogue_realtime.py   # GET    /api/v1/dialogues/recent (초기 로그 조회)
│   │                          # DELETE /api/v1/dialogues/recent (로그 초기화)
│   │                          # WS     /api/v1/dialogues/ws (대화 실시간 push)
│   │                          # append_dialogue_message() — 모든 대화 메모리+WS 기록
│   └── websocket.py           # 빈 stub
├── ai_mcp/
│   ├── llm_parser.py          # ★NLU 핵심 — 규칙 숏컷 4가지 → Claude Haiku → validator
│   ├── parser.py              # 키워드 규칙 파서 (PARSER_MODE=rule 시 사용)
│   ├── clarifier.py           # 재질문 답변 처리 (AsyncAnthropic, max 5턴)
│   ├── prompt.py              # AI_PARSER_SYSTEM_PROMPT, AI_CLARIFIER_SYSTEM_PROMPT
│   ├── validator.py           # LLM 결과 검증 (tool_name, device_name, enum, range 대조)
│   └── session_store.py       # save_parse_session() — dialogue_sessions UPSERT
├── core/
│   ├── state_manager.py       # DeviceStates 싱글톤 (in-memory), broadcast_state()
│   │                          # apply_device_control() — 직접 제어용 (legacy)
│   └── ws_manager.py          # WebSocketManager 싱글톤 — /ws/device-states 용
├── db/
│   └── database.py            # SQLAlchemy engine, SessionLocal, get_db()
├── schemas/
│   └── edge_dto.py            # CommandRequest (parse 엔드포인트용 DTO)
├── services/
│   ├── ai_service.py          # legacy wrapper (미사용)
│   └── dialogue_service.py    # legacy
~~mcp/~~                           # 삭제됨 — 실제 MCP 서버 미운용, 기능이 commands.py로 대체되어 제거

database/
├── smart_home_aiot_full.sql   # 전체 DB 덤프 (MySQL 8.0.45)
├── schema.sql
└── sample_queries.sql
```

---

## 4. API 엔드포인트 전체 목록

| Method | Path | 역할 | 파일 |
|--------|------|------|------|
| GET | / | 헬스체크 | main.py |
| GET | /api/v1/db/health | DB 연결 확인 | main.py |
| GET | /api/v1/mcp/resources/device-states | 기기 상태 조회 (DB) | mcp.py |
| GET | /api/v1/mcp/tools | MCP tool 목록 + input_schema (DB) | mcp.py |
| GET | /api/v1/routines | 루틴 목록 | routines.py |
| GET | /api/v1/routines/{name} | 루틴 상세 + steps | routines.py |
| POST | /api/v1/commands/parse | NLU 파싱만 (실행 없음) | edge.py |
| POST | /api/v1/dialogues/clarify | 재질문 답변 처리만 (실행 없음) | edge.py |
| **POST** | **/api/v1/commands/process** | **파싱+실행 통합 ★권장** | command_process.py |
| POST | /api/v1/commands/process-clarify | 명시적 재질문 답변+실행 | command_process.py |
| POST | /api/v1/commands/execute | commands 실행+DB+WebSocket | commands.py |
| POST | /api/v1/command/execute | legacy 직접 제어 (NLU 없음) | main.py |
| GET | /api/v1/devices/state | in-memory 기기 상태 | main.py |
| GET | /api/v1/dialogues/recent | 최근 대화 로그 (초기 로드) | dialogue_realtime.py |
| DELETE | /api/v1/dialogues/recent | 대화 로그 초기화 (데모용) | dialogue_realtime.py |
| WS | /ws/device-states | 기기 상태 실시간 (ws_manager) | main.py |
| WS | /ws | legacy 전체 state 브로드캐스트 | main.py |
| WS | /api/v1/dialogues/ws | 대화 로그 실시간 push | dialogue_realtime.py |

---

## 5. 요청/응답 스키마

### POST /api/v1/commands/process (CommandProcessRequest)
```json
{
  "session_id": "sess-xxxxxxxx",   // 선택 — 없으면 client_id로 pending 세션 자동 검색
  "client_id": "device-uuid",      // 선택 — 프론트엔드 기기 식별자
  "device_id": "front-device-id",  // 필수
  "raw_text": "에어컨 22도로 해줘", // raw_text 또는 stt_text 중 하나 필수
  "stt_text": null,
  "source": "frontend"             // 선택 (기본값 "frontend")
}
```

### 응답 — 실행 완료 (status: "executed")
```json
{
  "status": "executed",
  "mode": "parse",
  "session_id": "sess-xxxxxxxx",
  "clarification_needed": false,
  "response_text": "거실 에어컨 온도를 22도로 설정할게요.",
  "parse_result": { "intent": "device_control", "commands": [...] },
  "execute_result": {
    "success": true,
    "executed_commands": [{"step_order": 1, "device_name": "...", "tool_name": "...", "status": "success"}],
    "updated_states": [{"device_name": "...", "device_type": "...", "state": {...}}],
    "response_text": "..."
  }
}
```

### 응답 — 재질문 대기 (status: "waiting_clarification")
```json
{
  "status": "waiting_clarification",
  "mode": "parse",
  "session_id": "sess-xxxxxxxx",
  "clarification_needed": true,
  "clarification_question": "에어컨을 몇 도로 맞춰드릴까요?",
  "response_text": "에어컨을 몇 도로 맞춰드릴까요?",
  "pending_command": { ... }
}
```

### 응답 — 취소 (status: "cancelled")
```json
{
  "status": "cancelled",
  "mode": "cancel_pending",
  "session_id": "sess-xxxxxxxx",
  "clarification_needed": false,
  "response_text": "이전 요청을 취소했어요."
}
```

### POST /api/v1/commands/execute (ExecuteCommandRequest)
```json
{
  "session_id": "sess-xxxxxxxx",
  "raw_user_input": "에어컨 켜줘",
  "intent": "device_control",
  "response_text": "거실 에어컨을 켤게요.",
  "commands": [
    {
      "step_order": 1,
      "device_name": "living_room_aircon",
      "device_type": "air_conditioner",
      "tool_name": "air_conditioner.set_power",
      "parameters": {"power": "on"}
    }
  ]
}
```

---

## 6. 명령 처리 파이프라인 상세 (command_process.py)

```
POST /api/v1/commands/process
  │
  ├─ raw_text 추출: raw_text 없으면 stt_text 사용, 둘 다 없으면 400 에러
  │
  ├─ session_id 결정 (_resolve_session_id):
  │    1. 요청에 session_id 있으면 그대로 사용
  │    2. client_id로 DB에서 pending/waiting_clarification 세션 검색
  │    3. 없으면 새 생성: f"sess-{uuid4().hex[:8]}"
  │
  ├─ append_dialogue_message(role="user", ...) → 대화 로그 기록 + WS push
  │
  ├─ _try_load_pending_command(session_id):
  │    ├─ DB에서 pending_command 조회
  │    ├─ TTL(30초) 초과 → status="expired", pending_command=NULL, 반환 None
  │    └─ 유효하면 {session_id, pending_command, clarification_turn, last_intent} 반환
  │
  ├─ [pending 있을 때]:
  │    ├─ _is_cancel_pending_text(raw_text):
  │    │    → 취소어 포함 시 pending 취소 + "이전 요청을 취소했어요." 반환
  │    │
  │    ├─ _is_new_command_different_from_pending(raw_text, pending_command):
  │    │    → 다른 기기 명령 감지 시:
  │    │       1. pending 취소 (_clear_pending_command)
  │    │       2. 새 session_id로 새 명령 파싱 (_process_parse_flow)
  │    │       3. response_text 앞에 "이전 요청은 취소하고," 접두어
  │    │
  │    └─ 재질문 답변 처리 (_process_clarification_flow):
  │         ├─ clarify_natural_language() → Claude Haiku (AsyncAnthropic)
  │         ├─ clarification_needed=true → _update_pending_command + 재질문 반환
  │         └─ clarification_needed=false → execute_commands() + broadcast_state() + _clear_pending_command
  │
  └─ [pending 없을 때 — 새 명령 파싱] (_process_parse_flow):
       ├─ PARSER_MODE=llm → parse_with_llm()
       ├─ PARSER_MODE=rule → parse_natural_language()
       ├─ clarification_needed=true:
       │    ├─ commands 있으면 즉시 실행 (예: 공기청정기 켜기)
       │    └─ 재질문 응답 반환 (status: "waiting_clarification")
       └─ clarification_needed=false:
            ├─ commands 없으면 info_response 반환
            └─ execute_commands() 실행 후 응답

  모든 분기 완료 후: append_dialogue_message(role="assistant", ...) → WS push
```

**Pending TTL:** 30초 (`PENDING_TTL_SECONDS = 30`)

---

## 7. NLU 파싱 — 규칙 숏컷 4가지 (llm_parser.py)

Claude 호출 전 우선 처리됨. 다른 기기 키워드 함께 있으면 LLM에 위임.

### 숏컷 1: 에어컨 풍량 (`_is_ac_fan_speed_request`)
- **조건:** 풍량 키워드 + (에어컨 컨텍스트 키워드 OR 풍량 액션 키워드)
- **풍량 키워드 → 값:**
  - 강풍/강하게/바람 세게 → `"high"`
  - 중풍/중간풍/중간/중간 바람/중간세기 → `"medium"`
  - 약풍/약하게/바람 약하게 → `"low"`
  - 자동 풍량/자동풍 → `"auto"`
- **결과:** `air_conditioner.set_fan_speed` 즉시 실행

### 숏컷 2: 로봇청소기 구역 지정 청소 (`_is_vacuum_zone_request`)
- **조건:** 청소 키워드(청소/돌려/청소해 등) + 구역명
- **구역 매핑:** 거실→living_room, 주방/부엌→kitchen, 침실1→bedroom1, 침실2→bedroom2, 침실3→bedroom3, 세탁실→laundry, 전체/집 전체→all
- **결과:** `robot_vacuum.set_zone` + `robot_vacuum.set_action(action="start_cleaning")` 실행
- **다중 구역 지원:** `zone=["kitchen", "bedroom1"]`

### 숏컷 3: 로봇청소기 구역 미지정 (`_is_vacuum_no_zone_request`)
- **조건:** 청소기 관련 키워드(청소기/청소해/더럽 등) + 구역명 없음
- **결과:** `clarification_question="어디를 청소할까요? (예: 거실, 주방, 침실, 전체)"` 반환

### 숏컷 4: 애매한 더움 표현 (`_is_ambiguous_hot_request`)
- **조건:** `덥/더워/시원하게` 포함 + 온도(`\d{2}\s*도`) 없음 + 명시적 에어컨 on/off 없음
- **기본 결과:** `clarification_question="에어컨을 몇 도로 맞춰드릴까요?"` 반환
- **공기질 문제 동반 시** (냄새/쾌쾌/퀴퀴/먼지/공기 나빠/숨막혀/답답해/환기):
  - 공기청정기 즉시 켜기(set_power=on, set_mode=auto) + 에어컨 온도 재질문
  - `clarification_needed=true`, `commands=[air_purifier commands]`

숏컷 없으면 → Claude Haiku 호출 → validator 검증 → session_store 저장

---

## 8. LLM 파서 호출 흐름 (llm_parser.py: parse_with_llm)

```python
# 1. Claude Haiku 호출 시 전달하는 user payload
user_payload = {
    "user_input": raw_text,          # 사용자 자연어 입력
    "session_id": session_id,
    "device_id": device_id,
    "source": source,
    "mcp_tools": tools_data,         # DB의 모든 tool 정의 (input_schema 포함)
    "device_states": states_data,    # DB의 현재 기기 상태
    "routines": routines_data,       # 루틴 목록
}

# 2. Anthropic 동기 클라이언트 사용 (parse_with_llm은 sync Anthropic)
client = Anthropic()
message = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1200,
    temperature=0,
    system=AI_PARSER_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": json.dumps(user_payload)}]
)

# 3. 결과 처리
# JSON 파싱 실패 → parse_error, clarification_needed=true
# 검증 실패 (validator) → validation_error, clarification_needed=true
# 정상 → save_parse_session() → 결과 반환
```

---

## 9. 재질문 처리 (clarifier.py: clarify_natural_language)

```python
# AsyncAnthropic 비동기 클라이언트 사용
client = AsyncAnthropic()

user_payload = {
    "user_answer": user_answer,        # 사용자의 재질문 답변
    "pending_command": pending_command # 이전에 저장된 pending 정보
}

# max_tokens=1024, temperature=0
# CLARIFICATION_MAX_TURN = 5 초과 시 즉시 반환:
# intent="clarification_limit", commands=[], clarification_needed=False
# response_text="명확한 요청이 아닙니다. 처음부터 다시 말씀해 주세요."
```

---

## 10. LLM 결과 검증 (validator.py: validate_llm_parse_result)

검증 로직:
1. `clarification_needed=True`면 commands가 비어도 통과
2. 각 command에 대해:
   - `device_name`이 DB 기기 목록에 없으면 → 실패
   - `tool_name`이 DB tool 목록에 없으면 → 실패
   - required 파라미터 누락 → 실패
   - 알 수 없는 파라미터 키 → 실패
   - `enum` 값 벗어남 → 실패
   - `minimum`/`maximum` 범위 벗어남 → 실패
3. 검증 실패 시 → `intent="validation_error"`, `clarification_needed=True` 반환

---

## 11. session_store.py: save_parse_session

```python
# dialogue_sessions 테이블에 UPSERT
# clarification_needed=True → status="pending", pending_command=JSON, turn 유지
# clarification_needed=False → status="active", pending_command=NULL, turn=0
# db=None이면 DB 저장 건너뜀 (테스트 호환)
```

---

## 12. execute_commands 실행 흐름 (commands.py)

```
1. commands를 step_order 순서로 정렬
2. 각 command에 대해:
   a. DB에서 devices + device_types + commands + device_states 조인 조회
      → device_name, device_type, tool_name 모두 일치 + is_active=true 확인
      → 없으면 404 에러
   b. device_states.state_data(JSON) 로드
   c. apply_command_to_state(state, tool_name, parameters) → 새 state 계산
   d. device_states 테이블 UPDATE (state_data, updated_at=NOW())
   e. command_logs 테이블 INSERT
3. db.commit()
4. in-memory DeviceStates 싱글톤 동기화 (device_type으로 state 객체 접근 후 setattr)
5. broadcast_state() → /ws WebSocket으로 전체 상태 전송
6. ws_manager.broadcast(device_state_update) → /ws/device-states 로 기기별 상태 전송
```

**ws_manager.broadcast 메시지 형식:**
```json
{
  "type": "device_state_update",
  "device_name": "living_room_aircon",
  "device_type": "air_conditioner",
  "display_name": "거실 에어컨",
  "location": "거실",
  "state": {"power": "on", "temperature": 22, ...},
  "source": "ai_command",
  "response_text": "거실 에어컨 온도를 22도로 설정할게요."
}
```

---

## 13. apply_command_to_state 전체 매핑표 (commands.py)

| tool_name | parameter | DB 상태 필드 | 비고 |
|-----------|-----------|-------------|------|
| `*.set_power` | `power` | `power` | tv on 시 volume 기본값 유지 |
| `air_conditioner.set_temperature` | `temperature` | `temperature` | **18~30 범위만 허용, 벗어나면 ValueError** |
| `air_conditioner.set_mode` | `mode` | `mode` | cool/heat/dry/fan |
| `air_conditioner.set_fan_speed` | `fan_speed` | `fan_speed` | auto/low/medium/high |
| `air_conditioner.set_louver_angle` | `louver_angle` | `louver_angle` | up/mid/down/swing |
| `air_conditioner.set_timer` | `delay_minutes` | `timer` (dict) | |
| `light.set_brightness` | `brightness` | `brightness` | |
| `light.set_color` | `color` | `color` | |
| `light.set_color_temperature` | `color_temperature` | `color_temperature` | |
| `light.set_scene` | `scene_name` | `scene_name` | |
| `tv.set_volume` | `volume` | `volume` | 0~100 |
| `tv.set_channel` | `channel` | `channel` (str), power="on", content_name=None | |
| `tv.open_app` | `app_name` | `app_name`, `content_name`, power="on" | |
| `tv.play_content` | `content_title`, `app_name`(선택) | `content_name`, `app_name`(선택), power="on" | |
| `oven.set_temperature` | `target_temp` | `target_temp` | 30~250 |
| `oven.set_mode` | `mode` | `mode` | bake/convection_roast 등 |
| `oven.set_fan_speed` | `fan_speed` | `fan_speed` | |
| `oven.set_steam` | `steam` | `steam` | on/off |
| `oven.set_probe_target` | `probe_target` | `probe_temp` | |
| `air_purifier.set_mode` | `mode` | `mode` | auto/manual/sleep |
| `air_purifier.set_fan_speed` | `fan_speed` | `fan_speed` | |
| `washing_machine.set_action` | `action` | `status` | start→"washing", stop/pause→"stopped", resume→"washing" |
| `washing_machine.set_mode` | `mode` | `mode` | standard/delicate/heavy/wool 등 |
| `washing_machine.set_spin_speed` | `spin_speed` | `spin_speed` | low/medium/high |
| `washing_machine.set_water_temperature` | `water_temperature` | `water_temperature` | 0~95 |
| `washing_machine.set_reservation` | `start_time` | `reservation_time` | |
| `robot_vacuum.set_action` | `action` | `status` | start_cleaning→"cleaning", pause→"paused", return_to_dock→"returning" |
| `robot_vacuum.set_zone` | `zone` | `zone` | str 또는 list[str] |
| `robot_vacuum.set_suction_power` | `suction_power` | `suction_power` | quiet/standard/strong/max |
| `robot_vacuum.set_cleaning_mode` | `cleaning_mode` | `cleaning_mode` | auto/zigzag/spot/edge |
| 미등록 tool_name | — | — | `ValueError: Unsupported tool_name` |

---

## 14. DeviceStates Pydantic 모델 (state_manager.py)

```python
class AirConditionerState(BaseModel):
    power: str = "off"
    temperature: int = 24
    mode: str = "cool"         # cool, heat, dry, fan
    fan_speed: str = "auto"    # auto, low, medium, high
    louver_angle: str = "mid"  # up, mid, down, swing

class TVState(BaseModel):
    power: str = "off"
    volume: int = 10
    channel: Optional[str] = None
    content_name: Optional[str] = None

class AirPurifierState(BaseModel):
    power: str = "off"
    mode: str = "auto"           # auto, manual, sleep
    fan_speed: str = "low"
    air_quality: str = "good"
    pm25: int = 15
    filter_status: str = "clean"

class RobotVacuumState(BaseModel):
    status: str = "docked"       # idle, cleaning, paused, returning, docked, error
    battery_pct: int = 100
    zone: Optional[Union[str, List[str]]] = None
    suction_power: str = "standard"   # quiet, standard, strong, max
    cleaning_mode: str = "auto"       # auto, zigzag, spot, edge
    cleaned_area_m2: float = 0.0
    position: Position = Position()   # x: float, y: float
    do_not_disturb: bool = False
    error: Optional[str] = None

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

class LightState(BaseModel):             # DB 인스턴스 없음, 모델만 존재
    power: str = "off"
    brightness: int = 70
    color: str = "white"
    color_temperature: int = 4000
    scene_name: Optional[str] = "relax"

class DeviceStates(BaseModel):           # 전역 싱글톤: device_states = DeviceStates()
    air_conditioner: AirConditionerState = AirConditionerState()
    tv: TVState = TVState()
    air_purifier: AirPurifierState = AirPurifierState()
    robot_vacuum: RobotVacuumState = RobotVacuumState()
    oven: OvenState = OvenState()
    washing_machine: WashingMachineState = WashingMachineState()
    light: LightState = LightState()
```

---

## 15. DB 스키마 핵심 테이블

```sql
device_types (id, name, description, is_active)
  -- 7가지: air_conditioner, tv, robot_vacuum, air_purifier, oven, washing_machine, light

devices (id, device_type_id, name, display_name, location, is_active)
  -- 6개 인스턴스 (light 제외)

device_states (id, device_id UNIQUE, state_data JSON, updated_at)
  -- 기기당 1행, state_data는 JSON 문자열

commands (id, device_type_id, tool_name UNIQUE, action_name, description, is_active)

command_parameters (id, command_id, param_name, param_type, is_required,
                    default_value, allowed_values JSON, min_value, max_value, description)

routines (id, name, description, trigger_condition, is_active)
routine_steps (id, routine_id, step_order, command_id, parameters JSON, delay_seconds)

dialogue_sessions (
    id, session_id VARCHAR UNIQUE,
    messages JSON,                     -- 대화 이력
    status VARCHAR,                    -- active/pending/waiting_clarification/expired
    pending_command JSON,              -- 재질문 대기 중인 명령 정보
    clarification_turn INT,            -- 현재 재질문 턴 (0이면 재질문 없음)
    last_intent VARCHAR,               -- 마지막 intent
    client_id VARCHAR,                 -- 프론트엔드 기기 식별자
    source VARCHAR,                    -- "frontend" / "edge" 등
    created_at, updated_at
)

command_logs (
    id, session_id, device_id, command_id,
    raw_user_input TEXT,
    input_params JSON,
    parsed_command JSON,
    result JSON,
    status VARCHAR,                    -- "success" / "error"
    error_message TEXT,
    executed_at
)
```

---

## 16. 등록된 기기 목록 (DB 고정값 — 절대 변경 금지)

| device_name | device_type | display_name | location |
|-------------|-------------|--------------|----------|
| `living_room_aircon` | `air_conditioner` | 거실 에어컨 | 거실 |
| `living_room_tv` | `tv` | 거실 TV | 거실 |
| `living_room_air_purifier` | `air_purifier` | 거실 공기청정기 | 거실 |
| `living_room_robot_vacuum` | `robot_vacuum` | 거실 로봇청소기 | 거실 |
| `kitchen_oven` | `oven` | 주방 오븐 | 주방 |
| `utility_room_washing_machine` | `washing_machine` | 다용도실 세탁기 | 다용도실 |

> **light** 타입은 `commands` DB에 존재하지만 `devices` 인스턴스 없음. `state_manager.py`에만 `LightState` 존재.
> 각 기기는 시스템에 1개씩만 존재. "에어컨" = 항상 `living_room_aircon`.

---

## 17. LLM commands JSON 구조 (실행 전 필수 형식)

### 실행 가능 (clarification_needed=false)
```json
{
  "session_id": "sess-xxxxxxxx",
  "intent": "device_control",
  "commands": [
    {
      "step_order": 1,
      "device_name": "living_room_aircon",
      "device_type": "air_conditioner",
      "tool_name": "air_conditioner.set_power",
      "parameters": {"power": "on"}
    },
    {
      "step_order": 2,
      "device_name": "living_room_aircon",
      "device_type": "air_conditioner",
      "tool_name": "air_conditioner.set_temperature",
      "parameters": {"temperature": 22}
    }
  ],
  "clarification_needed": false,
  "clarification_turn": 0,
  "clarification_question": null,
  "pending_command": null,
  "response_text": "거실 에어컨을 켜고 22도로 설정할게요."
}
```

### 재질문 — 단일 기기 (clarification_needed=true)
```json
{
  "session_id": "sess-xxxxxxxx",
  "intent": "device_control",
  "commands": [],
  "clarification_needed": true,
  "clarification_turn": 1,
  "clarification_question": "에어컨을 몇 도로 맞춰드릴까요?",
  "pending_command": {
    "device_name": "living_room_aircon",
    "device_type": "air_conditioner",
    "inferred_intent": "cooling",
    "context_trigger": "hot",
    "candidate_tools": ["air_conditioner.set_power", "air_conditioner.set_mode", "air_conditioner.set_temperature"],
    "known_parameters": {"power": "on", "mode": "cool"},
    "missing_parameters": ["temperature"]
  },
  "response_text": "에어컨을 몇 도로 맞춰드릴까요?"
}
```

### 재질문 — 다중 기기 선택 (target_devices 방식)
```json
{
  "intent": "emotional_comfort",
  "commands": [],
  "clarification_needed": true,
  "clarification_turn": 1,
  "clarification_question": "시원하게 에어컨을 켜드릴까요, TV를 틀어드릴까요, 아니면 둘 다?",
  "pending_command": {
    "context_trigger": "emotional_comfort",
    "missing_parameters": ["comfort_preference"],
    "target_devices": [
      {
        "device_name": "living_room_tv",
        "device_type": "tv",
        "candidate_tools": ["tv.set_power"],
        "known_parameters": {"power": "on"}
      },
      {
        "device_name": "living_room_aircon",
        "device_type": "air_conditioner",
        "candidate_tools": ["air_conditioner.set_power", "air_conditioner.set_mode"],
        "known_parameters": {"power": "on", "mode": "cool"}
      }
    ]
  },
  "response_text": "기분이 안 좋으시군요. 에어컨이나 TV를 켜드릴까요?"
}
```

---

## 18. 대화 WebSocket (dialogue_realtime.py) 상세

**메모리 저장:** `_dialogue_logs: list[DialogueMessage]` (MAX_LOGS=300, 재시작 시 초기화)

**접속 즉시 수신 (dialogue_snapshot):**
```json
{"type": "dialogue_snapshot", "messages": [...최근 100개 DialogueMessage]}
```

**이후 실시간 push (dialogue_message):**
```json
{
  "type": "dialogue_message",
  "message": {
    "id": 5,
    "session_id": "sess-xxxxxxxx",
    "client_id": "device-uuid",
    "device_id": "front-id",
    "role": "user",              // user / assistant
    "source": "frontend",        // frontend / backend
    "text": "에어컨 22도로 해줘",
    "status": null,              // executed / waiting_clarification / cancelled 등
    "mode": null,                // parse / clarify / cancel_pending 등
    "clarification_needed": null,
    "timestamp": "2026-06-13T10:00:00"
  }
}
```

**`append_dialogue_message()` 호출 위치:**
- `/api/v1/commands/process` → user 입력 직후, 최종 응답 직후
- `/api/v1/commands/process-clarify` → user 답변 직후, 최종 응답 직후

---

## 19. WebSocket 3중 구조

| WebSocket | 경로 | 관리 | 용도 |
|-----------|------|------|------|
| ws_manager (WebSocketManager) | `/ws/device-states` | `active_connections: list` | 기기별 상태 업데이트 JSON |
| websocket_connections | `/ws` | `state_manager.py` 전역 list | 전체 DeviceStates JSON 브로드캐스트 (legacy) |
| _dialogue_ws_connections | `/api/v1/dialogues/ws` | `dialogue_realtime.py` 전역 list | 대화 메시지 실시간 push |

---

## 20. 상태 이중 저장 구조

```
명령 실행 시:
  1. MySQL device_states.state_data 업데이트 (execute_commands → apply_command_to_state)
  2. in-memory DeviceStates 싱글톤 동기화 (execute_commands 내 setattr)
  3. broadcast_state() → /ws 전체 상태 전송
  4. ws_manager.broadcast() → /ws/device-states 기기별 상태 전송

주의: in-memory는 서버 재시작 시 초기화됨.
     DB의 state_data가 영구 저장소.
```

---

## 21. 주요 Intent 값

| intent | 의미 |
|--------|------|
| `device_control` | 단일 기기 제어 |
| `multi_device_control` | 복수 기기 제어 |
| `routine_control` | 루틴 실행 |
| `device_query` | 기기 정보 조회 (commands 없음, response_text만) |
| `emotional_comfort` | 감정 표현 → 공감+제안 (pending으로 재질문) |
| `clarification_limit` | 5턴 초과 → 처음부터 다시 |
| `parse_error` | LLM JSON 파싱 실패 |
| `validation_error` | DB 규격 검증 실패 |

---

## 22. 취소어 목록 (command_process.py)

```python
CANCEL_WORDS = [
    "취소", "취소해", "그만", "그만해", "됐어", "됐습니다",
    "아니야", "안 해", "안해", "하지마", "필요없어", "필요 없어"
]
```

기기 감지 키워드 (`DEVICE_KEYWORDS`, 다른 기기 명령 여부 판단용):
```python
{
    "air_conditioner": ["에어컨", "냉방", "난방", "제습"],
    "light": ["불", "조명", "전등", "등"],
    "tv": ["tv", "TV", "티비", "텔레비전"],
    "robot_vacuum": ["청소기", "로봇청소기", "청소"],
    "air_purifier": ["공기청정기", "공청기"],
    "washing_machine": ["세탁기", "빨래"],
    "oven": ["오븐"],
}
```

---

## 23. AI 프롬프트 핵심 규칙 요약

### Parser (AI_PARSER_SYSTEM_PROMPT) 주요 규칙
- 등록된 6개 기기 이름만 사용
- "중풍" = 반드시 에어컨 fan_speed "medium" (뇌졸중 아님)
- 감정 표현 → `intent="emotional_comfort"`, 공감+선택지 제안, pending에 target_devices 리스트
- "둘 다" 답변 → target_devices 전체 즉시 실행 (재질문 없음)
- 세탁기: 옷감 유형 자동 감지 → mode/water_temperature/spin_speed 자동 설정
- 오븐: 음식 자동 감지 → target_temp/mode 자동 설정 (30~250°C 정수)
- TV: 장르·분위기로 요청 → AI가 직접 콘텐츠 추천 후 즉시 실행 (재질문 금지)
- 채널(KBS/MBC 등) → `tv.play_content(content_title="KBS")` (`tv.set_channel` 사용 안 함)
- 볼륨 ↑↓ → `tv.set_volume`에 현재보다 10 높거나 낮은 절대값
- 온도 범위 기기 구분: 18~30°C=에어컨, 30~250°C=오븐
- 켜진 기기 기준으로 후속 명령 추론 (device_states 확인 필수)
- `response_text`: 이모티콘 금지, 볼드체 금지, 특수기호 금지

### Clarifier (AI_CLARIFIER_SYSTEM_PROMPT) 주요 규칙
- `known_parameters` 그대로 유지, `missing_parameters` 사용자 답변에서 추출
- `candidate_tools` 전체에 대해 각각 command 생성
- `target_devices` 있으면 사용자가 선택한 기기에 commands 생성
- "둘 다/전부/모두" → target_devices 전체 즉시 실행
- emotional_comfort: 재질문 금지, known_parameters 그대로 즉시 실행
- TV 콘텐츠 존재 여부 AI 지식으로 검증 (없으면 재질문)
- max 5턴 → `intent="clarification_limit"`, 처음부터 다시

---

## 24. 루틴 목록 (DB 기준)

| 이름 | 내용 |
|------|------|
| `sleep` | 취침 루틴 |
| `away` | 외출 루틴 |
| `movie` | 영화 감상 루틴 |

---

## 25. 코드 작성 시 반드시 지킬 규칙

1. **기기 이름 고정** — `living_room_aircon`, `living_room_tv` 등 DB 등록 이름만 사용. 새 기기 추가 시 DB에 먼저 등록.
2. **PARSER_MODE** — 환경변수로 `llm`/`rule` 전환. 현재 `llm` 사용 중.
3. **상태 이중 업데이트** — DB(`device_states`) + in-memory 싱글톤 둘 다 업데이트해야 WebSocket이 최신 상태 전송.
4. **대화 로그** — `append_dialogue_message()` 로 user 입력과 assistant 응답 모두 기록 (현재 메모리, 재시작 시 초기화).
5. **pending TTL** — 30초 초과 시 자동 expire. 취소어/다른 기기 명령으로도 cancel.
6. **재질문 최대 5턴** — `CLARIFICATION_MAX_TURN = 5`.
7. **에어컨 온도 범위** — 18~30°C만 허용. `apply_command_to_state`에서 ValueError 발생.
8. **Claude 모델** — 기본 `claude-haiku-4-5-20251001`. Parser는 동기 `Anthropic()`, Clarifier는 비동기 `AsyncAnthropic()`.
9. **response_text 형식** — 이모티콘 금지, 마크다운 금지 (프롬프트 규칙).
10. **DB 연결** — `get_db()` 의존성 주입 사용. raw SQL은 `text()` 래핑.
11. **라우터 등록** — `main.py`에서 모든 router `include_router`.
12. **`apply_command_to_state`에 미등록 tool_name** → `ValueError` 발생. 새 tool 추가 시 이 함수도 수정 필요.

---

*이 문서는 2026-06-13 기준 feat/jimin 브랜치 상태를 직접 코드를 읽고 작성했습니다.*
