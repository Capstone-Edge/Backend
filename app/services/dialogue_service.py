"""
대화 상태 관리: 멀티턴 재질문 흐름 추적
"""
from typing import Optional, Dict, Any
import uuid

# 세션별 대화 상태 저장 (메모리 내)
sessions: Dict[str, Dict[str, Any]] = {}

def create_session() -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "history": [],
        "pending_context_trigger": None,
        "clarification_turn": 0,
    }
    return session_id

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return sessions.get(session_id)

def update_session_history(session_id: str, role: str, content: str):
    if session_id in sessions:
        sessions[session_id]["history"].append({"role": role, "content": content})
        if len(sessions[session_id]["history"]) > 20:
            sessions[session_id]["history"] = sessions[session_id]["history"][-20:]

def set_pending_clarification(session_id: str, context_trigger: str):
    if session_id in sessions:
        sessions[session_id]["pending_context_trigger"] = context_trigger
        sessions[session_id]["clarification_turn"] += 1

def clear_pending_clarification(session_id: str):
    if session_id in sessions:
        sessions[session_id]["pending_context_trigger"] = None
        sessions[session_id]["clarification_turn"] = 0

def get_pending_context_trigger(session_id: str) -> Optional[str]:
    session = sessions.get(session_id)
    if session:
        return session.get("pending_context_trigger")
    return None

def get_history(session_id: str) -> list:
    session = sessions.get(session_id)
    if session:
        return session.get("history", [])
    return []
