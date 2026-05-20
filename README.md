# SmartHome AIoT - Backend

스마트홈 음성 명령을 처리하는 FastAPI 백엔드 서버입니다.  
Claude AI 기반 NLU로 자연어 명령을 분석해 에어컨, TV, 공기청정기, 로봇청소기를 제어합니다.

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py               # FastAPI 진입점
│   ├── api/v1/
│   │   ├── edge.py           # 명령 파싱 라우터
│   │   └── websocket.py      # WebSocket 라우터
│   ├── core/
│   │   └── state_manager.py  # 기기 상태 관리
│   ├── mcp/
│   │   └── server.py         # FastMCP 기기 제어 Tools
│   ├── schemas/
│   │   └── edge_dto.py       # 요청/응답 모델
│   └── services/
│       ├── ai_service.py     # Claude NLU 파싱
│       └── dialogue_service.py # 멀티턴 대화 세션
├── requirements.txt
└── .env                      # 본인이 직접 생성 (아래 참고)
```

## 로컬 실행 방법

### 1. 레포 클론

```bash
git clone https://github.com/Capstone-Edge/Backend.git
cd Backend
```

### 2. 가상환경 생성 및 활성화

```bash
# 생성
python -m venv venv

# 활성화 (Windows)
venv\Scripts\activate

# 활성화 (Mac/Linux)
source venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

루트에 `.env` 파일을 직접 생성하고 아래 내용을 채웁니다.  
API 키는 팀원에게 별도로 받으세요.

```
ANTHROPIC_API_KEY=여기에_API_키_입력
```

### 5. 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 정상 실행되면 아래 주소에서 확인할 수 있습니다.

- API 문서: http://localhost:8000/docs
- 상태 확인: http://localhost:8000/

## 주요 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/command/parse` | 자연어 명령 파싱 및 기기 제어 |
| POST | `/api/v1/dialogue/clarify` | 재질문 답변 처리 |
| POST | `/api/v1/command/execute` | 직접 기기 제어 |
| GET | `/api/v1/devices/state` | 전체 기기 상태 조회 |
| WS | `/ws` | 실시간 상태 업데이트 |
