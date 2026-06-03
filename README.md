# Smarthome AIoT Backend

자연어 기반 스마트홈 AIoT 제어 시스템의 Backend 서버입니다.

현재 프로젝트는 기존에 분리되어 있던 `AI_MCP_Server` 기능을 Backend 내부로 통합하여, 하나의 FastAPI 서버에서 전체 흐름을 처리합니다.

---

## 1. 현재 실행 구조

현재 서버는 하나만 실행합니다.

```bash
uvicorn app.main:app --reload --port 8000
```

기존 `AI_MCP_Server` 레포는 보관용으로 남아 있지만, 현재 실행 흐름에서는 사용하지 않습니다.

즉, 현재 구조는 다음과 같습니다.

```text
Edge / Frontend
    ↓
Backend FastAPI Server
    ↓
내부 AI/MCP Parser
    ↓
DB 기반 MCP Tool / Resource / Routine 조회
    ↓
명령 검증 및 실행
    ↓
device_states 업데이트
    ↓
command_logs 저장
    ↓
WebSocket으로 Frontend 상태 동기화
```

---

## 2. Backend의 역할

Backend는 다음 역할을 담당합니다.

- Edge 또는 Frontend로부터 자연어 명령 수신
- 내부 AI/MCP Parser를 통해 자연어 명령 분석
- DB에 저장된 MCP Tool 목록 조회
- DB에 저장된 현재 Device State 조회
- DB에 저장된 Routine 목록 및 상세 조회
- AI/MCP Parser가 생성한 commands 검증
- 검증된 명령을 기준으로 device_states 업데이트
- command_logs 저장
- dialogue_sessions 기반 재질문 흐름 관리
- WebSocket을 통한 Frontend 실시간 상태 동기화

---

## 3. 핵심 원칙

현재 Backend는 아래 원칙을 기준으로 동작합니다.

1. DB는 기기별 명령 사전 역할을 한다.
2. AI/MCP Parser는 DB에 정의된 명령과 파라미터 규격 안에서만 commands를 생성한다.
3. 최종 실행 권한은 Backend가 가진다.
4. Backend는 commands를 검증한 뒤 device_states를 업데이트한다.
5. 명령 실행 결과는 command_logs에 저장한다.
6. 변경된 기기 상태는 WebSocket을 통해 Frontend에 전송한다.
7. 모호한 명령은 즉시 실행하지 않고 재질문 흐름을 거친다.
8. Backend, DB, Frontend는 동일한 명명 규칙을 사용한다.

---

## 4. 기술 스택

| 구분 | 기술 |
| --- | --- |
| Framework | FastAPI |
| Server | Uvicorn |
| Language | Python |
| Database | MySQL |
| API Docs | Swagger UI |
| Realtime Sync | WebSocket |
| Environment | python-dotenv |

---

## 5. 실행 방법

### 5.1 가상환경 생성

```bash
python -m venv venv
```

### 5.2 가상환경 활성화

Windows PowerShell 기준:

```bash
.\venv\Scripts\activate
```

### 5.3 패키지 설치

```bash
pip install -r requirements.txt
```

### 5.4 환경 변수 설정

Backend 루트 경로에 `.env` 파일을 생성합니다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=본인_MySQL_비밀번호
DB_NAME=smart_home_aiot
PARSER_MODE=llm
```

실제 LLM API를 연결할 경우 아래 항목을 추가할 수 있습니다.

```env
OPENAI_API_KEY=본인_OPENAI_API_KEY
```

또는

```env
ANTHROPIC_API_KEY=본인_ANTHROPIC_API_KEY
```

현재 Mock Parser 기반 테스트에서는 LLM API Key가 필요하지 않습니다.

### 5.5 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

### 5.6 Swagger 접속

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:8000/docs
```

---

## 6. 현재 주요 API

### 6.1 DB 상태 확인

| Method | URL | 설명 |
| --- | --- | --- |
| GET | `/api/v1/db/health` | MySQL 연결 상태 확인 |

### 6.2 MCP 조회 API

| Method | URL | 설명 |
| --- | --- | --- |
| GET | `/api/v1/mcp/tools` | DB 기반 MCP Tool 목록 조회 |
| GET | `/api/v1/mcp/resources/device-states` | 현재 기기 상태 조회 |
| GET | `/api/v1/routines` | 루틴 목록 조회 |
| GET | `/api/v1/routines/{routine_name}` | 특정 루틴 상세 조회 |

### 6.3 사용자 명령 처리 API

| Method | URL | 설명 |
| --- | --- | --- |
| POST | `/api/v1/commands/parse` | 자연어 명령 분석 |
| POST | `/api/v1/dialogues/clarify` | 재질문 응답 처리 |
| POST | `/api/v1/commands/execute` | 명령 검증 및 실행 |

### 6.4 Frontend 동기화 API

| Method | URL | 설명 |
| --- | --- | --- |
| WS | `/ws/device-states` | 기기 상태 변경 실시간 전송 |

---

## 7. 현재 지원 기기

현재 MVP 기준 지원 기기는 다음과 같습니다.

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

## 8. 현재 지원 Tool 목록

### 8.1 Air Conditioner

| action_name | tool_name | 설명 |
| --- | --- | --- |
| set_power | `air_conditioner.set_power` | 에어컨 전원 ON/OFF |
| set_temperature | `air_conditioner.set_temperature` | 설정 온도 변경 |
| set_mode | `air_conditioner.set_mode` | 냉방, 난방, 제습, 송풍, 자동 모드 변경 |
| set_fan_speed | `air_conditioner.set_fan_speed` | 풍량 조절 |
| set_louver_angle | `air_conditioner.set_louver_angle` | 바람 방향 조절 |
| set_timer | `air_conditioner.set_timer` | 예약 실행 또는 예약 종료 |

### 8.2 Light

| action_name | tool_name | 설명 |
| --- | --- | --- |
| set_power | `light.set_power` | 조명 전원 ON/OFF |
| set_brightness | `light.set_brightness` | 밝기 조절 |
| set_color | `light.set_color` | 색상 변경 |
| set_color_temperature | `light.set_color_temperature` | 색온도 변경 |
| set_scene | `light.set_scene` | 수면, 집중, 영화, 휴식 모드 설정 |

### 8.3 TV

| action_name | tool_name | 설명 |
| --- | --- | --- |
| set_power | `tv.set_power` | TV 전원 ON/OFF |
| set_volume | `tv.set_volume` | TV 볼륨 설정 |
| set_channel | `tv.set_channel` | TV 채널 설정 |
| open_app | `tv.open_app` | Netflix, YouTube 등 앱 실행 |
| play_content | `tv.play_content` | 사용자가 말한 콘텐츠명 재생 또는 표시 |

---

## 9. 주요 동작 흐름

### 9.1 명확한 명령 처리

예시 입력:

```text
나는솔로 틀어줘
```

처리 흐름:

```text
POST /api/v1/commands/parse
    ↓
내부 AI/MCP Parser가 TV 명령으로 변환
    ↓
commands 배열 반환
    ↓
POST /api/v1/commands/execute
    ↓
living_room_tv 상태 업데이트
    ↓
WebSocket으로 Frontend에 상태 전송
```

예상 commands:

```json
[
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
]
```

---

### 9.2 재질문 흐름

예시 입력:

```text
집이 너무 덥네
```

처리 흐름:

```text
POST /api/v1/commands/parse
    ↓
온도 정보 부족 판단
    ↓
clarification_needed = true 반환
    ↓
사용자 추가 응답 수신
    ↓
POST /api/v1/dialogues/clarify
    ↓
최종 commands 생성
```

예상 재질문 응답:

```json
{
  "clarification_needed": true,
  "clarification_question": "에어컨을 몇 도로 맞춰드릴까요?",
  "pending_command": {
    "device_name": "living_room_aircon",
    "device_type": "air_conditioner",
    "inferred_intent": "cooling",
    "context_trigger": "hot",
    "candidate_tools": [
      "air_conditioner.set_power",
      "air_conditioner.set_mode",
      "air_conditioner.set_temperature"
    ],
    "known_parameters": {
      "power": "on",
      "mode": "cool"
    },
    "missing_parameters": [
      "temperature"
    ]
  }
}
```

사용자 추가 응답:

```text
24도로 해줘
```

예상 최종 commands:

```json
[
  {
    "step_order": 1,
    "device_name": "living_room_aircon",
    "device_type": "air_conditioner",
    "tool_name": "air_conditioner.set_power",
    "parameters": {
      "power": "on"
    }
  },
  {
    "step_order": 2,
    "device_name": "living_room_aircon",
    "device_type": "air_conditioner",
    "tool_name": "air_conditioner.set_mode",
    "parameters": {
      "mode": "cool"
    }
  },
  {
    "step_order": 3,
    "device_name": "living_room_aircon",
    "device_type": "air_conditioner",
    "tool_name": "air_conditioner.set_temperature",
    "parameters": {
      "temperature": 24
    }
  }
]
```

---

### 9.3 루틴 처리 흐름

예시 입력:

```text
영화 모드로 해줘
```

처리 흐름:

```text
POST /api/v1/commands/parse
    ↓
routine_control 판단
    ↓
GET /api/v1/routines/movie 기준 commands 생성
    ↓
POST /api/v1/commands/execute
    ↓
TV, 조명, 에어컨 상태 순차 업데이트
    ↓
WebSocket으로 Frontend에 상태 전송
```

---

## 10. WebSocket 메시지 형식

명령 실행 후 Backend는 Frontend로 다음 형식의 메시지를 전송합니다.

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

Frontend는 `device_name`, `device_type`, `state` 값을 기준으로 시뮬레이터 상태를 갱신합니다.

---

## 11. 테스트 완료 항목

현재 아래 항목까지 테스트가 완료되었습니다.

- MySQL 연결 확인
- DB Health API 확인
- MCP Tool 목록 조회 확인
- Device State 조회 확인
- Routine 목록 조회 확인
- Routine 상세 조회 확인
- 자연어 명령 Parse 확인
- 재질문 Clarify 흐름 확인
- Command Execute 확인
- device_states 업데이트 확인
- command_logs 저장 확인
- Backend 단일 서버 실행 확인
- WebSocket 상태 동기화 확인

---

## 12. 현재 실행 기준

현재는 다음 서버 하나만 실행하면 됩니다.

```bash
uvicorn app.main:app --reload --port 8000
```

별도의 AI_MCP_Server 실행은 필요하지 않습니다.

기존 방식:

```text
Backend Server: 8000
AI_MCP_Server: 8001
```

현재 방식:

```text
Backend 단일 서버: 8000
```

---

## 13. 향후 작업

현재 Mock Parser 기반 전체 파이프라인 검증이 완료된 상태입니다.

다음 단계는 다음과 같습니다.

1. Frontend와 WebSocket 메시지 형식 최종 합의
2. Edge에서 STT 결과를 `/api/v1/commands/parse`로 전송
3. 실제 LLM API 연결
4. Mock Parser 로직을 LLM 기반 Parser로 교체
5. 자연어 테스트셋 확장
6. 최종 시연 시나리오 정리

---

## 14. 개발 메모

현재 AI/MCP 기능은 별도 서버가 아니라 Backend 내부 모듈로 통합되어 있습니다.

따라서 코드 수정 시 다음 사항을 지켜야 합니다.

- Backend가 자기 자신을 HTTP로 다시 호출하지 않도록 한다.
- `AI_MCP_BASE_URL`, `BACKEND_BASE_URL`, `AI_SERVER_PORT`는 현재 구조에서 사용하지 않는다.
- Parser, Clarify, Routine 변환 로직은 Backend 내부 service 계층에서 처리한다.
- 최종 명령 실행은 반드시 `/api/v1/commands/execute` 흐름을 기준으로 처리한다.
- DB 상태 변경 후에는 WebSocket broadcast가 수행되어야 한다.

---

## 15. Git 작업 기준

현재 작업 브랜치에서 README 수정 후 다음 순서로 커밋합니다.

```bash
git status
git add README.md
git commit -m "docs: update README for integrated backend server"
git push origin feat/minsu
```

이후 GitHub에서 `feat/minsu` 브랜치를 `dev` 브랜치로 Pull Request 생성합니다.
