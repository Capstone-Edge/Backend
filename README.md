# Backend

자연어 기반 스마트홈 AIoT 제어 시스템의 Backend 서버입니다.

Backend는 Edge 또는 Frontend로부터 사용자 명령을 수신하고, AI_MCP_Server에 자연어 해석을 요청한 뒤, 반환된 명령을 검증하고 실행합니다. 실행 결과는 MySQL DB에 저장되며, 변경된 기기 상태는 WebSocket을 통해 Frontend 시뮬레이터로 전송됩니다.

---

## 1. 역할

Backend는 전체 시스템의 중심 서버입니다.

주요 역할은 다음과 같습니다.

- Edge / Frontend 요청 수신
- AI_MCP_Server 호출
- DB 기반 MCP Tool / Resource / Routine API 제공
- AI가 생성한 commands 검증
- device_states 업데이트
- command_logs 저장
- dialogue_sessions 관리
- WebSocket을 통한 Frontend 상태 동기화

---

## 2. 전체 흐름

```text
사용자 음성 명령
→ Edge STT
→ Backend /api/v1/commands/parse
→ AI_MCP_Server /parse
→ Backend API로 Tool / Device State / Routine 조회
→ AI_MCP_Server가 commands 생성
→ Backend가 commands 검증 및 실행
→ MySQL device_states 업데이트
→ command_logs 저장
→ WebSocket으로 Frontend 상태 전송
```

---

## 3. 서버 실행 주소

```text
Backend        : http://127.0.0.1:8000
AI_MCP_Server  : http://127.0.0.1:8001
```

Swagger 문서:

```text
http://127.0.0.1:8000/docs
```

---

## 4. 기술 스택

| 구분 | 기술 |
|---|---|
| Framework | FastAPI |
| Language | Python |
| DB | MySQL |
| API Docs | Swagger / OpenAPI |
| Realtime Sync | WebSocket |
| AI Server 연동 | HTTP API |

---

## 5. 환경 변수

Backend 루트 경로에 `.env` 파일을 생성합니다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=본인_MySQL_비밀번호
DB_NAME=smart_home_aiot

AI_MCP_BASE_URL=http://127.0.0.1:8001
```

`.env` 파일은 GitHub에 올리지 않습니다.

---

## 6. 실행 방법

### 6.1 가상환경 생성 및 활성화

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 6.2 패키지 설치

```powershell
pip install -r requirements.txt
```

### 6.3 서버 실행

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 7. 주요 API

## 7.1 Health Check

### DB 연결 확인

```text
GET /api/v1/db/health
```

정상 응답 예시:

```json
{
  "status": "ok",
  "db_name": "smart_home_aiot"
}
```

---

## 7.2 사용자 명령 처리 API

| 기능 | Method | URL | 설명 |
|---|---|---|---|
| 명령 분석 | POST | `/api/v1/commands/parse` | 사용자 자연어 명령을 AI_MCP_Server로 전달하고 분석 결과를 반환 |
| 재질문 응답 처리 | POST | `/api/v1/dialogues/clarify` | pending_command와 사용자 추가 답변을 결합해 최종 명령 생성 |
| 명령 실행 | POST | `/api/v1/commands/execute` | AI가 생성한 commands를 검증 후 DB 상태 업데이트 |

---

## 7.3 MCP 조회용 API

AI_MCP_Server가 Backend DB 정보를 직접 조회하지 않고, 아래 API를 통해 필요한 정보를 가져갑니다.

| 기능 | Method | URL | 설명 |
|---|---|---|---|
| MCP Tool 목록 조회 | GET | `/api/v1/mcp/tools` | commands + command_parameters 기반 Tool Schema 반환 |
| MCP Resource 상태 조회 | GET | `/api/v1/mcp/resources/device-states` | 현재 기기 상태 반환 |
| 루틴 목록 조회 | GET | `/api/v1/routines` | 사용 가능한 루틴 목록 반환 |
| 루틴 상세 조회 | GET | `/api/v1/routines/{routine_name}` | 특정 루틴의 실행 step 목록 반환 |

---

## 7.4 Frontend 연동 API

| 기능 | Method | URL | 설명 |
|---|---|---|---|
| 기기 목록 조회 | GET | `/api/v1/devices` | Frontend 초기 렌더링용 기기 목록 |
| 특정 기기 상태 조회 | GET | `/api/v1/devices/{device_name}/state` | 특정 기기의 현재 상태 조회 |
| 기기 상태 실시간 동기화 | WS | `/ws/device-states` | 명령 실행 후 변경 상태를 Frontend에 전송 |

---

## 8. 현재 MVP 지원 기기

현재 1차 MVP 지원 기기는 다음 3개입니다.

```text
air_conditioner
light
tv
```

현재 등록된 실제 기기 인스턴스는 다음과 같습니다.

```text
living_room_aircon
living_room_light
living_room_tv
```

---

## 9. 명령 실행 Request 예시

```json
{
  "session_id": "sess-tv001",
  "raw_user_input": "나는솔로 틀어줘",
  "intent": "device_control",
  "commands": [
    {
      "step_order": 1,
      "device_name": "living_room_tv",
      "device_type": "tv",
      "tool_name": "tv.set_power",
      "parameters": {
        "power": "on"
      }
    },
    {
      "step_order": 2,
      "device_name": "living_room_tv",
      "device_type": "tv",
      "tool_name": "tv.play_content",
      "parameters": {
        "content_title": "나는솔로"
      }
    }
  ],
  "response_text": "TV를 켜고 나는솔로를 재생할게요."
}
```

---

## 10. 명령 실행 Response 예시

```json
{
  "success": true,
  "executed_commands": [
    {
      "step_order": 1,
      "device_name": "living_room_tv",
      "tool_name": "tv.set_power",
      "status": "success"
    },
    {
      "step_order": 2,
      "device_name": "living_room_tv",
      "tool_name": "tv.play_content",
      "status": "success"
    }
  ],
  "updated_states": [
    {
      "device_name": "living_room_tv",
      "device_type": "tv",
      "location": "living_room",
      "state": {
        "power": "on",
        "volume": 20,
        "channel": 1,
        "app_name": null,
        "content_title": "나는솔로"
      }
    }
  ],
  "response_text": "TV를 켜고 나는솔로를 재생할게요."
}
```

---

## 11. WebSocket 메시지 형식

Backend는 명령 실행 후 변경된 기기 상태를 Frontend에 아래 형식으로 전송합니다.

```json
{
  "type": "device_state_update",
  "device_name": "living_room_tv",
  "device_type": "tv",
  "display_name": "거실 TV",
  "location": "living_room",
  "state": {
    "power": "on",
    "volume": 20,
    "channel": 1,
    "app_name": null,
    "content_title": "나는솔로"
  },
  "source": "ai_command",
  "response_text": "TV를 켜고 나는솔로를 재생할게요."
}
```

---

## 12. 주의 사항

- AI_MCP_Server는 DB에 직접 접근하지 않습니다.
- Backend만 MySQL DB에 접근합니다.
- AI_MCP_Server는 Backend API를 통해 Tool, Device State, Routine 정보를 조회합니다.
- 최종 명령 검증과 실행은 Backend가 담당합니다.
- Frontend는 WebSocket으로 전달받은 표준 상태 JSON을 기준으로 화면을 갱신합니다.
- `.env` 파일은 GitHub에 올리지 않습니다.