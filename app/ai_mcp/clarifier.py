import json
import os
from anthropic import Anthropic
from app.ai_mcp.prompt import AI_CLARIFIER_SYSTEM_PROMPT

CLARIFICATION_MAX_TURN = 5

async def clarify_natural_language(
    session_id: str,
    user_answer: str,
    pending_command: dict | None = None,
    clarification_turn: int = 1,
):
    if clarification_turn >= CLARIFICATION_MAX_TURN:
        return {
            "session_id": session_id,
            "intent": "clarification_limit",
            "commands": [],
            "clarification_needed": False,
            "clarification_turn": clarification_turn,
            "clarification_question": None,
            "pending_command": None,
            "response_text": "명확한 요청이 아닙니다. 처음부터 다시 말씀해 주세요.",
        }

    client = Anthropic()
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    user_payload = {
        "user_answer": user_answer,
        "pending_command": pending_command or {},
    }

    message = client.messages.create(
        model=model_name,
        max_tokens=1024,
        temperature=0,
        system=AI_CLARIFIER_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": json.dumps(user_payload, ensure_ascii=False),
            }
        ],
    )

    raw_output = "\n".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    ).strip()

    try:
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```JSON", "").replace("```", "").strip()
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "session_id": session_id,
            "intent": "device_control",
            "commands": [],
            "clarification_needed": True,
            "clarification_turn": clarification_turn,
            "clarification_question": "다시 한 번 말씀해 주시겠어요?",
            "pending_command": pending_command,
            "response_text": "다시 한 번 말씀해 주시겠어요?",
        }

    result["session_id"] = session_id
    result.setdefault("intent", "device_control")
    result.setdefault("commands", [])
    result.setdefault("clarification_needed", False)
    result.setdefault("clarification_turn", clarification_turn)
    result.setdefault("clarification_question", None)
    result.setdefault("pending_command", None)
    result.setdefault("response_text", "")

    return result
