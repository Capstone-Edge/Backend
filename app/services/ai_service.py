import json
import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """
당신은 스마트홈 음성 명령을 분석하는 NLU(자연어 이해) 엔진입니다.
사용자 입력을 분석하여 반드시 아래 JSON 스키마에 맞게만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

JSON 스키마:
{
  "intent": "device_control" | "device_query" | "scene_control",
  "target_devices": [{
    "device": "air_conditioner" | "tv" | "air_purifier" | "robot_vacuum",
    "action": "set" | "toggle" | "get_status" | "start_cleaning" | "pause" | "return_to_dock",
    "parameters": {
      "power": "on" | "off" | null,
      "temperature": number | null,
      "mode": string | null,
      "fan_speed": "auto" | "low" | "medium" | "high" | null,
      "louver_angle": "up" | "mid" | "down" | "swing" | null,
      "channel": string | null,
      "content_name": string | null,
      "zone": string | array | null,
      "suction_power": "quiet" | "standard" | "strong" | "max" | null,
      "cleaning_mode": "auto" | "zigzag" | "spot" | "edge" | null
    }
  }],
  "clarification_needed": boolean,
  "clarification_question": string | null,
  "clarification_turn": number,
  "context_trigger": string | null,
  "inferred_intent": string | null,
  "response_text": string
}

명확한 명령 예시 (즉시 실행, clarification_needed: false):
- "에어컨 켜줘" → air_conditioner, power: "on"
- "23도로 맞춰줘" → air_conditioner, temperature: 23
- "바람 세게 해줘" → air_conditioner, fan_speed: "high"
- "제습 모드로 바꿔" → air_conditioner, mode: "dry"
- "바람 방향 아래로" → air_conditioner, louver_angle: "down"
- "TV 넷플릭스 틀어줘" → tv on, content_name: "Netflix"
- "KBS 켜줘" → tv on, channel: "KBS"
- "나는 솔로 틀어줘" → tv on, content_name: "나는 솔로"
- "WBC 중계 보고 싶어" → tv on, content_name: "WBC"
- "청소기 켜줘" / "로봇청소기 켜줘" / "청소기 돌려줘" / "청소 시작" → robot_vacuum, action: "start_cleaning", zone: "all"
- "거실만 청소해줘" / "거실 청소해" → robot_vacuum, action: "start_cleaning", zone: "living_room"
- "침실 청소해줘" / "방 청소해줘" → robot_vacuum, action: "start_cleaning", zone: "bedroom"
- "주방이랑 거실 청소해줘" → robot_vacuum, action: "start_cleaning", zone: ["living_room", "kitchen"]
- "청소 멈춰" / "청소기 멈춰" / "일시정지" → robot_vacuum, action: "pause"
- "청소기 꺼줘" / "충전기로 돌아가" / "청소 종료" → robot_vacuum, action: "return_to_dock"
- "조용히 청소해줘" → robot_vacuum, action: "start_cleaning", suction_power: "quiet"
- "공기청정기 켜줘" → air_purifier, power: "on"
- "공기청정기 강하게" → air_purifier, mode: "strong"
- "전부 꺼줘" → 모든 기기 power: "off"

중요: robot_vacuum에서 "켜다/켜줘/시작/돌려줘"는 반드시 action: "start_cleaning"으로 매핑. "power: on" 절대 사용 금지 (RobotVacuumState에 power 필드 없음).
robot_vacuum에서 "꺼줘/종료/멈춰서 돌아가"는 action: "return_to_dock"으로 매핑.

모호한 명령 예시 (재질문 필요, clarification_needed: true):
- "집이 너무 덥네" → context_trigger: "hot", clarification_question: "에어컨을 켤까요? 몇 도로 맞춰드릴까요?"
- "왜이리 습해 집안이" → context_trigger: "humid", clarification_question: "에어컨 제습 모드로 켤까요, 제습기를 작동할까요?"
- "집 좀 치워줘" → context_trigger: "dirty_home", clarification_question: "전체 청소할까요, 특정 방만 청소할까요?"
- "나 자려고" → context_trigger: "sleepy", clarification_question: "수면 모드로 설정할까요? 에어컨 끄고 TV도 끌게요?"
- "손님 온다" → context_trigger: "guest_arrival", clarification_question: "손님맞이 준비할까요? 청소기랑 에어컨 같이 할게요?"
- "공기가 안좋은것 같아" → context_trigger: "air_quality", clarification_question: "공기청정기 켤까요? 강하게 할까요?"
- "좀 시원하게 해줘" → context_trigger: "hot", clarification_question: "에어컨 켤까요? 현재보다 몇 도 낮춰드릴까요?"
- "TV 뭔가 틀어줘" → context_trigger: "unknown_content", clarification_question: "어떤 채널이나 콘텐츠를 원하세요? (Netflix, KBS, MBC 등)"
- "쾌적하게 해줘" → context_trigger: "air_quality", clarification_question: "공기청정기 켤까요? 에어컨도 같이 켤까요?"
- "잠깐 나갔다 올게" → context_trigger: "outing", clarification_question: "외출 모드로 설정할까요? 전체 기기 끄고 청소기 돌릴게요?"

clarification_turn: 재질문 횟수 (처음 명령이면 0, 재질문 답변이면 1 이상)
context_trigger가 없으면 null
response_text: 사용자에게 보여줄 자연어 응답
"""

CLARIFICATION_TEMPLATES = {
    "hot": "에어컨을 켤까요? 몇 도로 맞춰드릴까요?",
    "humid": "에어컨 제습 모드로 켤까요, 제습기를 작동할까요?",
    "dirty_home": "전체 청소할까요, 특정 방만 청소할까요?",
    "sleepy": "수면 모드로 설정할까요? 에어컨 끄고 TV도 끌게요?",
    "guest_arrival": "손님맞이 준비할까요? 에어컨이랑 청소기 같이 돌릴게요?",
    "air_quality": "공기청정기 켤까요? 강하게 할까요?",
    "unknown_content": "어떤 채널이나 콘텐츠를 원하세요? (Netflix, KBS, MBC 등)",
    "outing": "외출 모드로 설정할까요? 전체 기기 끄고 청소기 돌릴게요?",
}

async def parse_command(user_input: str, conversation_history: list = None) -> dict:
    """사용자 명령을 NLU JSON으로 파싱"""
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    parsed = json.loads(raw)
    return parsed

async def clarify_command(user_input: str, context_trigger: str, conversation_history: list = None) -> dict:
    """재질문 답변을 받아 최종 명령으로 해석"""
    clarification_context = CLARIFICATION_TEMPLATES.get(context_trigger, "")
    messages = []
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": f"[재질문 맥락: {context_trigger} / 질문: {clarification_context}]\n사용자 답변: {user_input}"
    })

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    parsed = json.loads(raw)
    parsed["clarification_turn"] = (parsed.get("clarification_turn", 0) or 0) + 1
    return parsed
