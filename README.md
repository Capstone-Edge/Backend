# 자연어 기반 스마트홈 AIoT 제어 시스템 - Backend

## 프로젝트 개요

본 Backend 서버는 자연어 기반 스마트홈 AIoT 제어 시스템의 중심 서버이다.

Edge 또는 Frontend로부터 사용자의 음성/텍스트 명령을 수신하고, AI 기반 자연어 해석 결과를 바탕으로 스마트홈 기기 상태를 갱신한다. 변경된 기기 상태는 WebSocket을 통해 Frontend 시뮬레이터에 실시간으로 동기화된다.

전체 흐름은 다음과 같다.

사용자 입력 → Edge STT 또는 Frontend 입력 → Backend 명령 처리 → AI 자연어 해석 → 명령 실행 → DB 상태 갱신 → WebSocket 상태 동기화

## 주요 기능

* 자연어 명령 수신 및 처리
* 명령 Parse / Execute 자동 파이프라인
* 모호한 명령에 대한 재질문 처리
* DB 기반 기기 상태 업데이트
* 명령 실행 로그 저장
* WebSocket 기반 Frontend 실시간 동기화
* MCP Tool / Resource / Routine 조회 API 제공

## 기술 스택

| 구분       | 기술         |
| -------- | ---------- |
| Backend  | FastAPI    |
| Language | Python     |
| Database | MySQL      |
| ORM      | SQLAlchemy |
| API Docs | Swagger UI |
| Realtime | WebSocket  |

## 실행 방법

### 1. 가상환경 생성 및 활성화

```
python -m venv venv
.\venv\Scripts\activate
```

### 2. 패키지 설치

```
pip install -r requirements.txt
```

### 3. MySQL DB 생성

```
CREATE DATABASE smart_home_aiot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 4. schema / seed 적용

```
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database\schema.sql
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database\seed.sql
```

### 5. 서버 실행

```
uvicorn app.main:app --reload
```

Swagger 문서:

```
http://127.0.0.1:8000/docs
```

## 핵심 API

| Method | URL                                 | 설명                  |
| ------ | ----------------------------------- | ------------------- |
| POST   | /api/v1/commands/process            | 자연어 명령 처리 메인 API    |
| GET    | /api/v1/mcp/tools                   | MCP Tool 목록 조회      |
| GET    | /api/v1/mcp/resources/device-states | 현재 기기 상태 조회         |
| GET    | /api/v1/routines                    | 루틴 목록 조회            |
| GET    | /api/v1/routines/{routine_name}     | 루틴 상세 조회            |
| WS     | /ws/device-states                   | Frontend 상태 실시간 동기화 |

## 메인 명령 처리 API

실제 Edge / Frontend 연동에서는 `/api/v1/commands/process`를 사용한다.

이 API는 기존의 parse, clarify, execute 흐름을 하나로 통합하여 처리한다.

처리 방식은 다음과 같다.

1. 명령이 명확하면 바로 실행한다.
2. 명령이 모호하면 재질문을 반환한다.
3. 재질문 답변이 들어오면 기존 pending_command와 결합하여 최종 명령을 실행한다.
4. 실행 결과는 DB에 저장하고 WebSocket으로 Frontend에 전달한다.

요청 예시:

```
{
  "client_id": "frontend-browser-001",
  "device_id": "frontend-test",
  "raw_text": "거실 에어컨 24도로 켜줘",
  "source": "frontend"
}
```

## 응답 상태

| status                | 의미        |
| --------------------- | --------- |
| executed              | 명령 실행 완료  |
| waiting_clarification | 재질문 필요    |
| cancelled             | 이전 요청 취소  |
| expired               | 재질문 대기 만료 |

## DB 구조

주요 테이블은 다음과 같다.

* device_types
* devices
* commands
* command_parameters
* device_states
* dialogue_sessions
* command_logs
* routines
* routine_steps

DB는 단순 저장소가 아니라 기기별 명령 사전 역할을 한다.
commands와 command_parameters를 기반으로 AI/MCP Server가 사용할 Tool Schema를 구성한다.

## WebSocket 동기화

명령 실행 후 변경된 기기 상태는 다음 WebSocket으로 Frontend에 전달된다.

```
/ws/device-states
```

메시지 예시:

```
{
  "type": "device_state_update",
  "device_name": "living_room_light",
  "device_type": "light",
  "display_name": "거실 조명",
  "location": "living_room",
  "state": {
    "power": "on",
    "brightness": 70,
    "color": "yellow"
  },
  "source": "ai_command",
  "response_text": "거실 조명을 노란색으로 켤게요."
}
```

## 개발 시 주의사항

* 실제 연동은 `/api/v1/commands/process`를 사용한다.
* `/parse`, `/execute`, `/process-clarify`는 개발 및 디버깅용이다.
* AI/MCP Server는 DB에 직접 접근하지 않고 Backend API를 통해 Tool, Resource, Routine 정보를 조회한다.
* Backend는 AI가 생성한 명령을 최종 검증한 뒤 실행한다.
* Frontend는 WebSocket으로 전달받은 표준 상태 JSON을 기준으로 화면을 갱신한다.
