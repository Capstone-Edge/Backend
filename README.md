# 자연어 기반 스마트홈 AIoT 제어 시스템 - Backend

본 저장소는 자연어 기반 스마트홈 AIoT 제어 시스템의 Backend 서버 구현을 포함한다.

사용자는 음성 또는 텍스트로 스마트홈 기기를 제어할 수 있으며, Backend는 사용자의 자연어 명령을 분석하고, DB에 정의된 기기별 명령 사전을 기반으로 실행 가능한 명령으로 변환한다. 이후 기기 상태를 갱신하고, 명령 실행 로그를 저장하며, WebSocket을 통해 Frontend 시뮬레이터에 실시간으로 상태 변경을 전송한다.

---

## 1. 프로젝트 개요

본 프로젝트는 사용자의 자연어 명령을 기반으로 스마트홈 기기를 제어하는 AIoT 시스템이다.

전체 흐름은 다음과 같다.

```text
사용자 음성/텍스트 명령
→ Edge STT 또는 Frontend 입력
→ Backend FastAPI Server
→ 내부 AI/MCP Parser
→ DB 기반 Tool / Resource / Routine 조회
→ 자연어 명령을 구조화된 command JSON으로 변환
→ Backend 명령 검증 및 실행
→ device_states 업데이트
→ command_logs 저장
→ WebSocket으로 Frontend 상태 동기화
```

Backend는 전체 시스템의 중심 서버 역할을 수행하며, 다음 기능을 담당한다.

* 자연어 명령 수신
* AI/MCP Parser 기반 명령 분석
* DB 기반 기기 명령 사전 조회
* 명령 파라미터 검증
* 기기 상태 업데이트
* 명령 실행 로그 저장
* 재질문 대화 세션 관리
* 루틴/모드 실행
* WebSocket 기반 실시간 상태 동기화

---

## 2. 핵심 설계 원칙

본 프로젝트의 핵심 설계 원칙은 다음과 같다.

1. DB는 단순 저장소가 아니라 기기별 명령 사전 역할을 한다.
2. commands와 command_parameters는 MCP Tool Schema 생성의 기준이 된다.
3. AI/MCP Parser는 DB에 정의된 명령과 파라미터 범위 안에서만 명령을 생성한다.
4. Backend는 AI/MCP Parser가 생성한 명령을 최종 검증하고 실행한다.
5. device_states는 현재 기기 상태를 저장하며, Frontend 상태 동기화의 기준이 된다.
6. dialogue_sessions는 재질문이 필요한 대화의 맥락과 pending_command를 저장한다.
7. command_logs는 명령 실행 이력과 실패 원인을 기록한다.
8. routines와 routine_steps는 수면 모드, 외출 모드, 영화 모드와 같은 복합 루틴을 관리한다.
9. Frontend는 Backend가 전달하는 표준 상태 JSON을 기준으로 2D/3D 시뮬레이터를 갱신한다.

---

## 3. 기술 스택

| 영역                | 기술                   |
| ----------------- | -------------------- |
| Backend Framework | FastAPI              |
| Language          | Python               |
| DBMS              | MySQL                |
| ORM / DB Driver   | SQLAlchemy / PyMySQL |
| API 문서            | Swagger UI           |
| 실시간 통신            | WebSocket            |
| 환경 변수 관리          | python-dotenv        |
| 실행 서버             | Uvicorn              |
| 협업                | GitHub               |

---

## 4. 현재 DBMS 및 데이터베이스 이름

현재 DBMS는 MySQL을 사용한다.

```sql
CREATE DATABASE smart_home_aiot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

현재 사용 중인 DB 이름은 다음과 같다.

```text
smart_home_aiot
```

---

## 5. 현재 DB 테이블 구성

현재 Backend는 총 9개의 테이블을 사용한다.

```text
command_logs
command_parameters
commands
device_states
device_types
devices
dialogue_sessions
routine_steps
routines
```

각 테이블의 역할은 다음과 같다.

| 테이블                | 역할                                 |
| ------------------ | ---------------------------------- |
| device_types       | 스마트홈 기기 종류를 정의한다.                  |
| devices            | 실제 설치된 기기 인스턴스를 정의한다.              |
| commands           | 기기별 실행 가능한 명령을 정의한다.               |
| command_parameters | 각 명령에 필요한 파라미터 규격을 정의한다.           |
| device_states      | 각 기기의 현재 상태를 JSON으로 저장한다.          |
| dialogue_sessions  | 사용자와 AI 사이의 대화 세션 및 재질문 상태를 저장한다.  |
| command_logs       | 명령 실행 이력, 실행 결과, 오류 메시지를 저장한다.     |
| routines           | 수면 모드, 외출 모드, 영화 모드 등 루틴 정보를 저장한다. |
| routine_steps      | 각 루틴이 수행해야 하는 세부 명령 단계를 저장한다.      |

---

## 6. 현재 지원 기기

현재 Backend는 총 7종의 스마트홈 기기를 지원한다.

```text
air_conditioner
air_purifier
light
oven
robot_vacuum
tv
washing_machine
```

현재 등록된 실제 기기 인스턴스는 다음과 같다.

| device_name                  | device_type     | display_name | location     |
| ---------------------------- | --------------- | ------------ | ------------ |
| living_room_aircon           | air_conditioner | 거실 에어컨       | living_room  |
| living_room_air_purifier     | air_purifier    | 거실 공기청정기     | living_room  |
| living_room_light            | light           | 거실 조명        | living_room  |
| kitchen_oven                 | oven            | 주방 오븐        | kitchen      |
| living_room_robot_vacuum     | robot_vacuum    | 거실 로봇청소기     | living_room  |
| living_room_tv               | tv              | 거실 TV        | living_room  |
| utility_room_washing_machine | washing_machine | 다용도실 세탁기     | utility_room |

---

## 7. 주요 API 목록

### 7.1 DB 상태 확인 API

| 기능          | Method | URL               |
| ----------- | ------ | ----------------- |
| DB 연결 상태 확인 | GET    | /api/v1/db/health |

### 7.2 MCP 조회 API

| 기능                 | Method | URL                                 |
| ------------------ | ------ | ----------------------------------- |
| MCP Tool 목록 조회     | GET    | /api/v1/mcp/tools                   |
| MCP Resource 상태 조회 | GET    | /api/v1/mcp/resources/device-states |

### 7.3 사용자 명령 처리 API

| 기능        | Method | URL                       |
| --------- | ------ | ------------------------- |
| 자연어 명령 분석 | POST   | /api/v1/commands/parse    |
| 명령 실행     | POST   | /api/v1/commands/execute  |
| 재질문 응답 처리 | POST   | /api/v1/dialogues/clarify |

### 7.4 루틴 API

| 기능       | Method | URL                             |
| -------- | ------ | ------------------------------- |
| 루틴 목록 조회 | GET    | /api/v1/routines                |
| 루틴 상세 조회 | GET    | /api/v1/routines/{routine_name} |

### 7.5 Frontend 실시간 동기화 API

| 기능            | Method | URL               |
| ------------- | ------ | ----------------- |
| 기기 상태 실시간 동기화 | WS     | /ws/device-states |

---

## 8. 실행 방법

### 8.1 저장소 클론

```bash
git clone https://github.com/Capstone-Edge/Backend.git
cd Backend
```

### 8.2 dev 브랜치로 이동

```bash
git switch dev
```

만약 로컬에 dev 브랜치가 없다면 다음 명령을 사용한다.

```bash
git fetch origin
git switch -c dev origin/dev
```

### 8.3 가상환경 생성 및 활성화

Windows PowerShell 기준:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

macOS / Linux 기준:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 8.4 패키지 설치

```bash
pip install -r requirements.txt
```

### 8.5 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성한다.

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_home_aiot
PARSER_MODE=llm
```

비밀번호는 본인 MySQL 환경에 맞게 수정한다.

### 8.6 MySQL DB 생성

MySQL 접속 후 다음 명령을 실행한다.

```sql
CREATE DATABASE smart_home_aiot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE smart_home_aiot;
```

### 8.7 DB 스키마 및 Seed 데이터 적용

프로젝트 루트에서 다음 명령을 실행한다.

```bash
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database/schema.sql
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database/seed.sql
```

필요 시 샘플 쿼리도 실행한다.

```bash
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database/sample_queries.sql
```

### 8.8 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버 실행 후 다음 주소에서 Swagger UI를 확인할 수 있다.

```text
http://127.0.0.1:8000/docs
```

---

## 9. DB 상태 확인 쿼리

### 9.1 테이블 목록 확인

```sql
SHOW TABLES;
```

예상 결과:

```text
command_logs
command_parameters
commands
device_states
device_types
devices
dialogue_sessions
routine_steps
routines
```

### 9.2 등록된 기기 목록 확인

```sql
SELECT
  d.name AS device_name,
  dt.name AS device_type,
  d.display_name,
  d.location
FROM devices d
JOIN device_types dt ON d.device_type_id = dt.id
ORDER BY dt.name, d.name;
```

예상 결과:

```text
living_room_aircon              air_conditioner  거실 에어컨      living_room
living_room_air_purifier        air_purifier     거실 공기청정기  living_room
living_room_light               light            거실 조명        living_room
kitchen_oven                    oven             주방 오븐        kitchen
living_room_robot_vacuum        robot_vacuum     거실 로봇청소기  living_room
living_room_tv                  tv               거실 TV          living_room
utility_room_washing_machine    washing_machine  다용도실 세탁기  utility_room
```

### 9.3 테이블별 데이터 개수 확인

```sql
SELECT COUNT(*) AS device_type_count FROM device_types;
SELECT COUNT(*) AS device_count FROM devices;
SELECT COUNT(*) AS command_count FROM commands;
SELECT COUNT(*) AS command_parameter_count FROM command_parameters;
SELECT COUNT(*) AS device_state_count FROM device_states;
SELECT COUNT(*) AS routine_count FROM routines;
SELECT COUNT(*) AS routine_step_count FROM routine_steps;
```

### 9.4 기기 타입별 명령 개수 확인

```sql
SELECT
  dt.name AS device_type,
  COUNT(c.id) AS command_count
FROM device_types dt
LEFT JOIN commands c ON c.device_type_id = dt.id
GROUP BY dt.name
ORDER BY dt.name;
```

### 9.5 현재 기기 상태 확인

```sql
SELECT
  d.name AS device_name,
  dt.name AS device_type,
  ds.state_data,
  ds.updated_at
FROM device_states ds
JOIN devices d ON ds.device_id = d.id
JOIN device_types dt ON d.device_type_id = dt.id
ORDER BY dt.name, d.name;
```

---

## 10. API 사용 예시

### 10.1 DB Health Check

Request:

```text
GET /api/v1/db/health
```

Response 예시:

```json
{
  "status": "ok",
  "database": "smart_home_aiot"
}
```

---

### 10.2 MCP Tool 목록 조회

Request:

```text
GET /api/v1/mcp/tools
```

설명:

DB의 `commands`, `command_parameters`, `device_types` 정보를 기반으로 AI/MCP Parser가 사용할 수 있는 Tool Schema 목록을 반환한다.

Response 예시:

```json
{
  "tools": [
    {
      "name": "air_conditioner.set_power",
      "device_type": "air_conditioner",
      "action_name": "set_power",
      "description": "에어컨 전원 ON/OFF",
      "input_schema": {
        "type": "object",
        "properties": {
          "power": {
            "type": "string",
            "enum": ["on", "off"],
            "description": "전원 상태"
          }
        },
        "required": ["power"]
      }
    }
  ]
}
```

특정 기기 타입만 조회할 수도 있다.

```text
GET /api/v1/mcp/tools?device_type=tv&is_active=true
```

---

### 10.3 MCP Resource 상태 조회

Request:

```text
GET /api/v1/mcp/resources/device-states
```

설명:

DB의 `devices`, `device_types`, `device_states` 정보를 기반으로 현재 기기 상태를 반환한다.

Response 예시:

```json
{
  "devices": [
    {
      "device_name": "living_room_aircon",
      "device_type": "air_conditioner",
      "display_name": "거실 에어컨",
      "location": "living_room",
      "state": {
        "power": "off",
        "temperature": 24,
        "mode": "cool",
        "fan_speed": "auto",
        "louver_angle": "mid"
      },
      "updated_at": "2026-05-20T12:00:00"
    }
  ]
}
```

---

## 11. 자연어 명령 분석 API

### 11.1 명확한 명령

Request:

```http
POST /api/v1/commands/parse
Content-Type: application/json
```

```json
{
  "session_id": "sess-demo-001",
  "device_id": "frontend-test",
  "raw_text": "거실 에어컨 24도로 켜줘",
  "source": "frontend"
}
```

Response 예시:

```json
{
  "session_id": "sess-demo-001",
  "intent": "device_control",
  "commands": [
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
      "tool_name": "air_conditioner.set_temperature",
      "parameters": {
        "temperature": 24
      }
    }
  ],
  "clarification_needed": false,
  "clarification_turn": 0,
  "clarification_question": null,
  "pending_command": null,
  "response_text": "거실 에어컨을 24도로 켤게요."
}
```

---

### 11.2 TV 콘텐츠 재생 명령

Request:

```json
{
  "session_id": "sess-tv-001",
  "device_id": "frontend-test",
  "raw_text": "나는솔로 틀어줘",
  "source": "frontend"
}
```

Response 예시:

```json
{
  "session_id": "sess-tv-001",
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
  "clarification_needed": false,
  "clarification_turn": 0,
  "clarification_question": null,
  "pending_command": null,
  "response_text": "TV를 켜고 나는솔로를 재생할게요."
}
```

---

### 11.3 특정 앱에서 콘텐츠 재생

Request:

```json
{
  "session_id": "sess-tv-002",
  "device_id": "frontend-test",
  "raw_text": "유튜브에서 뉴진스 틀어줘",
  "source": "frontend"
}
```

Response 예시:

```json
{
  "session_id": "sess-tv-002",
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
        "content_title": "뉴진스",
        "app_name": "youtube"
      }
    }
  ],
  "clarification_needed": false,
  "clarification_turn": 0,
  "clarification_question": null,
  "pending_command": null,
  "response_text": "TV를 켜고 유튜브에서 뉴진스를 재생할게요."
}
```

---

### 11.4 재질문이 필요한 명령

Request:

```json
{
  "session_id": "sess-hot-001",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

Response 예시:

```json
{
  "session_id": "sess-hot-001",
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
  },
  "response_text": "에어컨을 몇 도로 맞춰드릴까요?"
}
```

---

## 12. 재질문 응답 처리 API

Request:

```http
POST /api/v1/dialogues/clarify
Content-Type: application/json
```

```json
{
  "session_id": "sess-hot-001",
  "user_answer": "24도로 해줘"
}
```

Response 예시:

```json
{
  "session_id": "sess-hot-001",
  "intent": "device_control",
  "commands": [
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
  ],
  "clarification_needed": false,
  "clarification_turn": 1,
  "clarification_question": null,
  "pending_command": null,
  "response_text": "거실 에어컨을 24도 냉방으로 켤게요."
}
```

---

## 13. 명령 실행 API

Request:

```http
POST /api/v1/commands/execute
Content-Type: application/json
```

```json
{
  "session_id": "sess-demo-001",
  "raw_user_input": "거실 에어컨 24도로 켜줘",
  "intent": "device_control",
  "commands": [
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
      "tool_name": "air_conditioner.set_temperature",
      "parameters": {
        "temperature": 24
      }
    }
  ],
  "response_text": "거실 에어컨을 24도로 켤게요."
}
```

Response 예시:

```json
{
  "success": true,
  "executed_commands": [
    {
      "step_order": 1,
      "device_name": "living_room_aircon",
      "tool_name": "air_conditioner.set_power",
      "status": "success"
    },
    {
      "step_order": 2,
      "device_name": "living_room_aircon",
      "tool_name": "air_conditioner.set_temperature",
      "status": "success"
    }
  ],
  "updated_states": [
    {
      "device_name": "living_room_aircon",
      "device_type": "air_conditioner",
      "location": "living_room",
      "state": {
        "power": "on",
        "temperature": 24,
        "mode": "cool",
        "fan_speed": "auto",
        "louver_angle": "mid"
      }
    }
  ],
  "response_text": "거실 에어컨을 24도로 켤게요."
}
```

---

## 14. WebSocket 상태 동기화

Frontend는 다음 WebSocket 주소에 연결한다.

```text
ws://127.0.0.1:8000/ws/device-states
```

명령 실행 후 Backend는 변경된 기기 상태를 다음과 같은 JSON으로 전송한다.

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
    "app_name": "youtube",
    "content_title": "뉴진스"
  },
  "source": "ai_command",
  "response_text": "TV를 켜고 유튜브에서 뉴진스를 재생할게요."
}
```

Frontend는 `device_name`, `device_type`, `state` 값을 기준으로 시뮬레이터의 기기 상태를 갱신한다.

---

## 15. 루틴 API

### 15.1 루틴 목록 조회

Request:

```text
GET /api/v1/routines
```

Response 예시:

```json
{
  "routines": [
    {
      "routine_name": "sleep",
      "routine_display_name": "수면 모드",
      "description": "취침을 위해 조명과 에어컨을 조정하는 루틴",
      "is_active": true
    },
    {
      "routine_name": "away",
      "routine_display_name": "외출 모드",
      "description": "외출 시 주요 기기를 OFF 상태로 변경하는 루틴",
      "is_active": true
    },
    {
      "routine_name": "movie",
      "routine_display_name": "영화 모드",
      "description": "영화 감상을 위한 TV, 조명, 에어컨 제어 루틴",
      "is_active": true
    }
  ]
}
```

### 15.2 루틴 상세 조회

Request:

```text
GET /api/v1/routines/movie
```

Response 예시:

```json
{
  "routine_name": "movie",
  "routine_display_name": "영화 모드",
  "description": "영화 감상을 위한 TV, 조명, 에어컨 제어 루틴",
  "steps": [
    {
      "step_order": 1,
      "device_name": "living_room_tv",
      "device_type": "tv",
      "tool_name": "tv.set_power",
      "parameters": {
        "power": "on"
      },
      "delay_seconds": 0
    },
    {
      "step_order": 2,
      "device_name": "living_room_tv",
      "device_type": "tv",
      "tool_name": "tv.open_app",
      "parameters": {
        "app_name": "netflix"
      },
      "delay_seconds": 0
    },
    {
      "step_order": 3,
      "device_name": "living_room_light",
      "device_type": "light",
      "tool_name": "light.set_power",
      "parameters": {
        "power": "on"
      },
      "delay_seconds": 0
    },
    {
      "step_order": 4,
      "device_name": "living_room_light",
      "device_type": "light",
      "tool_name": "light.set_brightness",
      "parameters": {
        "brightness": 30
      },
      "delay_seconds": 0
    }
  ]
}
```

---

## 16. 주요 테스트 시나리오

### 16.1 에어컨 명시적 제어

```text
사용자: 거실 에어컨 24도로 켜줘
결과:
- living_room_aircon power = on
- temperature = 24
- WebSocket으로 에어컨 상태 변경 전송
```

### 16.2 조명 명시적 제어

```text
사용자: 거실 불 70퍼센트로 켜줘
결과:
- living_room_light power = on
- brightness = 70
- WebSocket으로 조명 상태 변경 전송
```

### 16.3 TV 콘텐츠 재생

```text
사용자: 나는솔로 틀어줘
결과:
- living_room_tv power = on
- content_title = 나는솔로
- WebSocket으로 TV 상태 변경 전송
```

### 16.4 TV 앱 기반 콘텐츠 재생

```text
사용자: 유튜브에서 뉴진스 틀어줘
결과:
- living_room_tv power = on
- app_name = youtube
- content_title = 뉴진스
- WebSocket으로 TV 상태 변경 전송
```

### 16.5 에어컨 재질문 루프

```text
사용자: 집이 너무 덥네
Backend: 에어컨을 몇 도로 맞춰드릴까요?
사용자: 24도로 해줘
결과:
- living_room_aircon power = on
- mode = cool
- temperature = 24
```

### 16.6 영화 모드 루틴

```text
사용자: 영화 모드로 해줘
결과:
- TV 전원 ON
- TV 앱 실행
- 조명 밝기 조절
- 에어컨 상태 조정
- 여러 기기 상태를 WebSocket으로 동기화
```

---

## 17. 개발 상태

현재 구현된 주요 기능은 다음과 같다.

| 기능                                | 상태    |
| --------------------------------- | ----- |
| MySQL DB 연결                       | 구현 완료 |
| 9개 테이블 기반 DB 구조                   | 구현 완료 |
| 7종 기기 Seed 데이터                    | 구현 완료 |
| 기기별 명령 사전                         | 구현 완료 |
| command_parameters 기반 Tool Schema | 구현 완료 |
| MCP Tool 목록 조회                    | 구현 완료 |
| MCP Resource 상태 조회                | 구현 완료 |
| 자연어 명령 Parse API                  | 구현 완료 |
| 재질문 Clarify API                   | 구현 완료 |
| 명령 Execute API                    | 구현 완료 |
| device_states 업데이트                | 구현 완료 |
| command_logs 저장                   | 구현 완료 |
| routines / routine_steps 조회       | 구현 완료 |
| WebSocket 상태 동기화                  | 구현 완료 |

---

## 18. 프로젝트 디렉토리 구조

예상 디렉토리 구조는 다음과 같다.

```text
Backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── commands.py
│   │       ├── dialogues.py
│   │       ├── mcp.py
│   │       ├── routines.py
│   │       └── websocket.py
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   ├── sample_queries.sql
│   └── smart_home_aiot_full.sql
├── requirements.txt
├── .env
└── README.md
```

---

## 19. Git 작업 흐름

### 19.1 현재 브랜치 확인

```bash
git branch
```

### 19.2 dev 브랜치 최신화

```bash
git switch dev
git pull origin dev
```

### 19.3 개인 작업 브랜치 생성

```bash
git switch -c feat/your-feature-name
```

예시:

```bash
git switch -c feat/minsu-update-readme
```

### 19.4 변경 파일 확인

```bash
git status
```

### 19.5 커밋

```bash
git add .
git commit -m "docs: update README for current MVP backend"
```

### 19.6 원격 브랜치 push

```bash
git push origin feat/minsu-update-readme
```

이후 GitHub에서 `feat/minsu-update-readme` → `dev` 방향으로 Pull Request를 생성한다.

---

## 20. 한 줄 요약

현재 Backend는 MySQL 기반 9개 테이블 구조를 사용하며, 에어컨, 공기청정기, 조명, 오븐, 로봇청소기, TV, 세탁기 총 7종 기기를 지원한다. Backend는 DB에 정의된 기기별 명령 사전과 파라미터 규격을 기반으로 자연어 명령을 분석하고, 명령 실행, 상태 갱신, 로그 저장, 재질문 처리, 루틴 실행, WebSocket 실시간 동기화를 수행하는 다중 기기 통합 제어 MVP 서버이다.
