# 자연어 기반 스마트홈 AIoT 제어 시스템 - Backend

## 1. 프로젝트 개요

본 Backend 서버는 자연어 기반 스마트홈 AIoT 제어 시스템의 중심 서버이다.

사용자의 음성 또는 텍스트 명령을 수신하고, AI/MCP 기반 자연어 해석 결과를 바탕으로 스마트홈 기기 상태를 갱신하며, 변경된 상태를 WebSocket을 통해 Frontend 시뮬레이터에 실시간으로 전달한다.

전체 시스템 흐름은 다음과 같다.

```text
사용자 음성/텍스트 입력
→ Edge STT 또는 Frontend 입력
→ Backend /api/v1/commands/process
→ 자연어 명령 Parse
→ 필요 시 Clarification 재질문 처리
→ 명령 Execute
→ device_states 업데이트
→ command_logs 저장
→ WebSocket으로 Frontend 상태 동기화
```

---

## 2. Backend 핵심 역할

Backend는 다음 역할을 담당한다.

```text
1. Edge / Frontend 요청 수신
2. 자연어 명령 Parse
3. 재질문이 필요한 명령의 pending_command 저장
4. 재질문 답변 Clarify 처리
5. 명령 실행 전 DB 기반 유효성 검증
6. device_states 업데이트
7. command_logs 저장
8. WebSocket을 통한 Frontend 상태 동기화
9. MCP Tool / Resource / Routine 조회 API 제공
```

---

## 3. 기술 스택

| 구분                | 기술                             |
| ----------------- | ------------------------------ |
| Backend Framework | FastAPI                        |
| Language          | Python                         |
| Database          | MySQL                          |
| ORM / DB Access   | SQLAlchemy                     |
| API Docs          | Swagger UI                     |
| Realtime Sync     | WebSocket                      |
| AI Parser         | Rule-based Parser / LLM Parser |
| Deployment        | Local / Docker 확장 가능           |

---

## 4. 현재 지원 기기

현재 Backend는 DB 명령 사전 기반으로 기기 명령을 처리한다.

현재 등록된 주요 기기 타입은 다음과 같다.

```text
air_conditioner
light
tv
air_purifier
robot_vacuum
washing_machine
oven
```

대표 기기 인스턴스는 다음과 같다.

```text
living_room_aircon
living_room_light
living_room_tv
living_room_air_purifier
living_room_robot_vacuum
utility_room_washing_machine
kitchen_oven
```

---

## 5. 주요 디렉터리 구조

```text
Backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── command_process.py
│   │       ├── commands.py
│   │       ├── edge.py
│   │       ├── mcp.py
│   │       ├── routines.py
│   │       └── ...
│   ├── ai_mcp/
│   │   ├── parser.py
│   │   ├── llm_parser.py
│   │   └── clarifier.py
│   ├── db/
│   │   └── database.py
│   └── schemas/
│       └── edge_dto.py
│
├── database/
│   ├── schema.sql
│   └── seed.sql
│
├── README.md
└── requirements.txt
```

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

### 6.3 MySQL DB 생성

```sql
CREATE DATABASE smart_home_aiot
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 6.4 schema 적용

```powershell
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database\schema.sql
```

### 6.5 seed 적용

```powershell
mysql --default-character-set=utf8mb4 -u root -p smart_home_aiot < database\seed.sql
```

### 6.6 서버 실행

```powershell
uvicorn app.main:app --reload
```

또는 `main.py` 직접 실행이 가능하도록 설정된 경우:

```powershell
python -m app.main
```

---

## 7. Swagger 접속

서버 실행 후 아래 주소에서 API 문서를 확인할 수 있다.

```text
http://127.0.0.1:8000/docs
```

---

## 8. 핵심 변경 사항: 자동 명령 처리 파이프라인

기존에는 자연어 명령을 처리하기 위해 다음 과정을 수동으로 수행해야 했다.

```text
1. POST /api/v1/commands/parse 호출
2. parse 결과의 commands 확인
3. clarification_needed=false이면 commands를 복사
4. POST /api/v1/commands/execute에 붙여넣어 실행
5. clarification_needed=true이면 clarify 후 다시 execute 호출
```

현재는 위 과정이 자동화되었다.

실제 Edge / Frontend 연동 시에는 아래 API 하나만 호출하면 된다.

```http
POST /api/v1/commands/process
```

Backend는 `/process` 내부에서 다음을 자동으로 판단한다.

```text
1. pending_command가 없으면 일반 자연어 명령으로 처리
2. 명령이 명확하면 parse 후 execute 자동 실행
3. 명령이 모호하면 pending_command 저장 후 재질문 반환
4. pending_command가 있으면 재질문 답변으로 판단
5. 재질문 답변이 완성되면 clarify 후 execute 자동 실행
6. 사용자가 취소 표현을 말하면 pending_command 삭제
7. 사용자가 다른 기기 명령을 말하면 기존 pending_command 취소 후 새 명령 처리
8. 오래된 pending_command는 자동 만료 처리
```

---

## 9. 실제 연동용 API

## 9.1 자동 명령 처리 API

```http
POST /api/v1/commands/process
```

### Request

```json
{
  "session_id": "sess-example-001",
  "client_id": "frontend-browser-001",
  "device_id": "frontend-test",
  "raw_text": "거실 에어컨 24도로 켜줘",
  "source": "frontend"
}
```

### Request 필드 설명

| 필드           | 필수 여부 | 설명                                 |
| ------------ | ----: | ---------------------------------- |
| `session_id` |    선택 | 기존 대화 세션 ID. 있으면 해당 세션을 사용한다.      |
| `client_id`  |    선택 | Frontend 브라우저, Edge 장치 등 클라이언트 식별자 |
| `device_id`  |    필수 | 요청을 보낸 장치 ID                       |
| `raw_text`   |    선택 | 사용자 자연어 입력                         |
| `stt_text`   |    선택 | Edge STT 결과. 기존 호환성을 위해 지원         |
| `source`     |    선택 | `frontend`, `edge` 등 입력 출처         |

`raw_text`와 `stt_text` 중 하나는 반드시 있어야 한다.

---

## 9.2 session_id 결정 규칙

Backend는 다음 순서로 세션을 결정한다.

```text
1. request.session_id가 있으면 해당 session_id 사용
2. session_id가 없고 client_id가 있으면 sess-{client_id} 사용
3. client_id도 없으면 sess-{device_id} 사용
```

예를 들어 다음 요청은:

```json
{
  "client_id": "frontend-browser-001",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

Backend 내부에서 아래 세션으로 처리된다.

```text
sess-frontend-browser-001
```

따라서 다음 요청에서도 같은 `client_id`를 보내면 `session_id`를 직접 보내지 않아도 재질문 흐름이 이어진다.

---

## 10. Response 주요 필드

`/api/v1/commands/process`의 응답에서는 `status`와 `mode`를 확인하면 현재 처리 상태를 알 수 있다.

### status

| 값                       | 의미                      |
| ----------------------- | ----------------------- |
| `executed`              | 명령이 최종 실행됨              |
| `waiting_clarification` | 재질문 필요. 사용자 답변 대기       |
| `cancelled`             | 사용자가 이전 pending 요청을 취소함 |
| `expired`               | 오래된 pending 요청이 만료됨     |

### mode

| 값                                     | 의미                                              |
| ------------------------------------- | ----------------------------------------------- |
| `parse`                               | 일반 자연어 명령으로 처리됨                                 |
| `clarify`                             | 기존 재질문에 대한 답변으로 처리됨                             |
| `cancel_pending`                      | pending_command가 취소됨                            |
| `new_command_after_pending_cancelled` | 재질문 대기 중 다른 기기 명령이 들어와 기존 pending을 취소하고 새 명령 처리 |

---

## 11. 시나리오별 동작 예시

## 11.1 명확한 명령

### Request

```json
{
  "client_id": "frontend-browser-001",
  "device_id": "frontend-test",
  "raw_text": "거실 불 켜줘",
  "source": "frontend"
}
```

### 처리 흐름

```text
/process
→ pending_command 없음
→ parse 수행
→ clarification_needed=false
→ execute 자동 실행
→ device_states 업데이트
→ WebSocket 전송
```

### Response 예시

```json
{
  "status": "executed",
  "mode": "parse",
  "session_id": "sess-frontend-browser-001",
  "clarification_needed": false,
  "response_text": "거실 조명을 켤게요.",
  "execute_result": {
    "success": true
  }
}
```

---

## 11.2 재질문이 필요한 명령

### Request

```json
{
  "client_id": "frontend-browser-002",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

### 처리 흐름

```text
/process
→ pending_command 없음
→ parse 수행
→ clarification_needed=true
→ dialogue_sessions.pending_command 저장
→ 재질문 반환
```

### Response 예시

```json
{
  "status": "waiting_clarification",
  "mode": "parse",
  "session_id": "sess-frontend-browser-002",
  "clarification_needed": true,
  "clarification_question": "에어컨을 몇 도로 맞춰드릴까요?",
  "response_text": "에어컨을 몇 도로 맞춰드릴까요?"
}
```

---

## 11.3 재질문 답변

### Request

```json
{
  "client_id": "frontend-browser-002",
  "device_id": "frontend-test",
  "raw_text": "24도로 해줘",
  "source": "frontend"
}
```

### 처리 흐름

```text
/process
→ 같은 client_id 기반 세션 조회
→ pending_command 있음
→ clarify 처리
→ commands 완성
→ execute 자동 실행
→ pending_command 삭제
```

### Response 예시

```json
{
  "status": "executed",
  "mode": "clarify",
  "session_id": "sess-frontend-browser-002",
  "clarification_needed": false,
  "response_text": "거실 에어컨을 24도 냉방으로 켤게요.",
  "execute_result": {
    "success": true
  }
}
```

---

## 11.4 재질문 중 취소

### Request

```json
{
  "client_id": "frontend-browser-003",
  "device_id": "frontend-test",
  "raw_text": "됐어 취소해",
  "source": "frontend"
}
```

### 처리 흐름

```text
/process
→ pending_command 있음
→ 취소 표현 감지
→ pending_command 삭제
→ 취소 응답 반환
```

### Response 예시

```json
{
  "status": "cancelled",
  "mode": "cancel_pending",
  "session_id": "sess-frontend-browser-003",
  "clarification_needed": false,
  "response_text": "이전 요청을 취소했어요."
}
```

---

## 11.5 재질문 중 다른 기기 명령

예를 들어 이전 pending이 에어컨 명령인데, 사용자가 조명 명령을 입력한 경우이다.

### Request

```json
{
  "client_id": "frontend-browser-004",
  "device_id": "frontend-test",
  "raw_text": "불 꺼줘",
  "source": "frontend"
}
```

### 처리 흐름

```text
/process
→ pending_command 있음
→ pending 기기: air_conditioner
→ 입력 기기: light
→ 기존 pending_command 삭제
→ "불 꺼줘"를 새 명령으로 parse
→ execute 자동 실행
```

### Response 예시

```json
{
  "status": "executed",
  "mode": "new_command_after_pending_cancelled",
  "session_id": "sess-frontend-browser-004",
  "clarification_needed": false,
  "response_text": "이전 요청은 취소하고, 거실 조명을 끌게요.",
  "execute_result": {
    "success": true
  }
}
```

---

## 12. pending_command 만료 정책

재질문 상태가 너무 오래 유지되면 사용자의 다음 입력을 잘못된 재질문 답변으로 처리할 수 있다.

이를 방지하기 위해 pending_command TTL을 적용한다.

```text
PENDING_TTL_SECONDS = 120
```

즉, 재질문 후 2분 이상 지나면 기존 `pending_command`는 만료 처리된다.

예시:

```text
사용자: 집이 너무 덥네
AI: 몇 도로 맞춰드릴까요?

2분 이상 경과

사용자: 불 켜줘
→ 에어컨 온도 답변으로 보지 않고, 조명 새 명령으로 처리
```

별도 DB 컬럼을 추가하지 않고, `dialogue_sessions.updated_at`을 기준으로 만료 여부를 판단한다.

---

## 13. 기존 API의 역할

기존 API는 삭제하지 않고 개발 및 디버깅용으로 유지한다.

| API                                     | 용도                            |
| --------------------------------------- | ----------------------------- |
| `POST /api/v1/commands/parse`           | 자연어 파싱 결과만 확인                 |
| `POST /api/v1/commands/execute`         | commands 실행만 단독 테스트           |
| `POST /api/v1/commands/process-clarify` | 재질문 처리만 단독 테스트                |
| `POST /api/v1/commands/process`         | 실제 Edge / Frontend 연동용 메인 API |

실제 서비스 연동에서는 `/api/v1/commands/process` 사용을 권장한다.

---

## 14. MCP 조회 API

AI/MCP Server는 DB에 직접 접근하지 않고 Backend API를 통해 Tool, Resource, Routine 정보를 조회한다.

## 14.1 MCP Tool 목록 조회

```http
GET /api/v1/mcp/tools
```

특정 기기 타입만 조회할 수 있다.

```http
GET /api/v1/mcp/tools?device_type=air_conditioner&is_active=true
```

---

## 14.2 MCP Resource 상태 조회

```http
GET /api/v1/mcp/resources/device-states
```

현재 등록된 기기 상태 목록을 반환한다.

---

## 14.3 루틴 목록 조회

```http
GET /api/v1/routines
```

---

## 14.4 루틴 상세 조회

```http
GET /api/v1/routines/{routine_name}
```

예시:

```http
GET /api/v1/routines/movie
```

---

## 15. WebSocket 상태 동기화

명령 실행 후 변경된 기기 상태는 WebSocket을 통해 Frontend로 전송된다.

```text
WS /ws/device-states
```

### 메시지 예시

```json
{
  "type": "device_state_update",
  "device_name": "living_room_light",
  "device_type": "light",
  "display_name": "거실 조명",
  "location": "living_room",
  "state": {
    "power": "on",
    "brightness": 70,
    "color": "yellow",
    "color_temperature": 4000,
    "scene_name": "relax"
  },
  "source": "ai_command",
  "response_text": "거실 조명을 노란색으로 켤게요."
}
```

---

## 16. DB 구조

현재 주요 테이블은 다음과 같다.

```text
device_types
devices
commands
command_parameters
device_states
dialogue_sessions
command_logs
routines
routine_steps
```

### 주요 역할

| 테이블                  | 설명                                |
| -------------------- | --------------------------------- |
| `device_types`       | 기기 타입 정의                          |
| `devices`            | 실제 기기 인스턴스 정의                     |
| `commands`           | 기기별 실행 가능한 명령 정의                  |
| `command_parameters` | 명령별 파라미터 규격 정의                    |
| `device_states`      | 현재 기기 상태 저장                       |
| `dialogue_sessions`  | 대화 세션, pending_command, 재질문 상태 저장 |
| `command_logs`       | 명령 실행 로그 저장                       |
| `routines`           | 사전 정의 루틴 목록                       |
| `routine_steps`      | 루틴별 세부 실행 단계                      |

---

## 17. dialogue_sessions 사용 방식

재질문이 필요한 명령은 `dialogue_sessions.pending_command`에 저장된다.

예시:

```json
{
  "device_name": "living_room_aircon",
  "device_type": "air_conditioner",
  "known_parameters": {
    "power": "on",
    "mode": "cool"
  },
  "missing_parameters": [
    "temperature"
  ]
}
```

이후 같은 `session_id`, `client_id`, `device_id` 기반 요청이 들어오면 Backend는 해당 입력을 재질문 답변으로 처리할지, 취소로 처리할지, 새 명령으로 처리할지 판단한다.

---

## 18. Frontend 연동 규칙

Frontend는 앞으로 다음 규칙을 따르면 된다.

```text
1. 사용자 입력은 항상 POST /api/v1/commands/process로 전송한다.
2. 가능하면 client_id를 고정해서 함께 보낸다.
3. response_text를 채팅 UI에 출력한다.
4. status가 waiting_clarification이면 사용자 답변을 기다린다.
5. 다음 입력도 동일하게 /process로 전송한다.
6. WebSocket으로 수신한 device_state_update를 기준으로 화면 상태를 갱신한다.
```

### Frontend Request 예시

```json
{
  "client_id": "frontend-browser-001",
  "device_id": "frontend-test",
  "raw_text": "거실 불 켜줘",
  "source": "frontend"
}
```

---

## 19. Edge 연동 규칙

Edge는 STT 결과를 Backend로 전송하고, Backend 응답의 `response_text`를 TTS로 출력한다.

```text
1. STT 결과를 raw_text 또는 stt_text로 전송한다.
2. client_id는 edge-pi-01처럼 고정한다.
3. 응답의 response_text를 TTS로 출력한다.
4. waiting_clarification 상태에서도 다음 음성 입력을 같은 /process API로 보낸다.
```

### Edge Request 예시

```json
{
  "client_id": "edge-pi-01",
  "device_id": "edge-pi-01",
  "stt_text": "집이 너무 덥네",
  "source": "edge"
}
```

또는:

```json
{
  "client_id": "edge-pi-01",
  "device_id": "edge-pi-01",
  "raw_text": "집이 너무 덥네",
  "source": "edge"
}
```

---

## 20. 개발용 테스트 시나리오

### 20.1 명확한 명령

```json
{
  "client_id": "test-direct-001",
  "device_id": "frontend-test",
  "raw_text": "거실 불 켜줘",
  "source": "frontend"
}
```

기대 결과:

```text
status = executed
mode = parse
clarification_needed = false
execute_result.success = true
```

---

### 20.2 재질문 후 실행

1차 요청:

```json
{
  "client_id": "test-hot-001",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

기대 결과:

```text
status = waiting_clarification
mode = parse
clarification_needed = true
```

2차 요청:

```json
{
  "client_id": "test-hot-001",
  "device_id": "frontend-test",
  "raw_text": "24도로 해줘",
  "source": "frontend"
}
```

기대 결과:

```text
status = executed
mode = clarify
clarification_needed = false
execute_result.success = true
```

---

### 20.3 재질문 중 취소

1차 요청:

```json
{
  "client_id": "test-cancel-001",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

2차 요청:

```json
{
  "client_id": "test-cancel-001",
  "device_id": "frontend-test",
  "raw_text": "됐어 취소해",
  "source": "frontend"
}
```

기대 결과:

```text
status = cancelled
mode = cancel_pending
pending_command = NULL
```

---

### 20.4 재질문 중 다른 기기 명령

1차 요청:

```json
{
  "client_id": "test-override-001",
  "device_id": "frontend-test",
  "raw_text": "집이 너무 덥네",
  "source": "frontend"
}
```

2차 요청:

```json
{
  "client_id": "test-override-001",
  "device_id": "frontend-test",
  "raw_text": "불 꺼줘",
  "source": "frontend"
}
```

기대 결과:

```text
status = executed
mode = new_command_after_pending_cancelled
pending_command = NULL
```

---

## 21. DB 확인용 SQL

### 21.1 특정 세션 확인

```sql
USE smart_home_aiot;

SELECT
  session_id,
  status,
  clarification_turn,
  pending_command,
  updated_at
FROM dialogue_sessions
WHERE session_id = 'sess-test-hot-001'\G
```

---

### 21.2 특정 기기 상태 확인

```sql
SELECT
  d.name,
  dt.name AS device_type,
  ds.state_data
FROM devices d
JOIN device_types dt ON d.device_type_id = dt.id
JOIN device_states ds ON d.id = ds.device_id
WHERE d.name = 'living_room_aircon'\G
```

---

### 21.3 명령 실행 로그 확인

```sql
SELECT
  id,
  session_id,
  raw_user_input,
  parsed_command,
  result,
  status,
  executed_at
FROM command_logs
WHERE session_id = 'sess-test-hot-001'
ORDER BY id DESC\G
```

---

## 22. 개발 시 주의사항

```text
1. 실제 연동은 /api/v1/commands/process를 사용한다.
2. /parse, /execute, /process-clarify는 디버깅용이다.
3. Frontend와 Edge는 가능하면 client_id를 고정해서 보낸다.
4. session_id가 없어도 client_id 또는 device_id 기반으로 세션을 이어간다.
5. pending_command는 2분 후 만료된다.
6. pending 상태에서 취소 표현이 들어오면 pending_command를 삭제한다.
7. pending 상태에서 다른 기기 명령이 들어오면 기존 pending을 취소하고 새 명령을 처리한다.
8. AI/MCP Parser는 DB에 정의된 tool_name과 parameter 규격을 따라야 한다.
9. Frontend는 WebSocket의 device_state_update를 기준으로 화면 상태를 갱신한다.
```

---

## 23. Git 작업 흐름

현재 작업 브랜치는 다음을 사용한다.

```text
feat/minsu
```

최신 원격 반영:

```powershell
git pull --rebase origin feat/minsu
```

변경 사항 커밋:

```powershell
git add .
git commit -m "feat: update backend command process pipeline"
```

원격 push:

```powershell
git push origin feat/minsu
```

충돌 발생 시:

```powershell
git status
code .
git add .
git rebase --continue
```

---

## 24. 한 줄 요약

현재 Backend는 `/api/v1/commands/process`를 중심으로 자연어 명령을 처리한다.
Frontend와 Edge는 사용자 입력을 항상 `/process`로 보내면 되며, Backend가 내부적으로 parse, clarify, execute, pending_command 저장/삭제, 세션 유지, 재질문 만료, 취소, 새 명령 전환까지 자동으로 처리한다.
