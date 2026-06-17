# LLM 재질문 pending_command 저장 공통화

import json
from sqlalchemy import text


def save_parse_session(
    db,
    session_id: str,
    intent: str,
    clarification_needed: bool,
    pending_command,
    clarification_turn: int,
):
    if db is None:
        return

    existing_session = db.execute(
        text("""
            SELECT id
            FROM dialogue_sessions
            WHERE session_id = :session_id
            LIMIT 1
        """),
        {"session_id": session_id},
    ).mappings().first()

    if clarification_needed:
        status = "pending"
        pending_command_json = json.dumps(pending_command or {}, ensure_ascii=False)
    else:
        status = "active"
        pending_command_json = None
        clarification_turn = 0

    if existing_session:
        db.execute(
            text("""
                UPDATE dialogue_sessions
                SET status = :status,
                    pending_command = :pending_command,
                    clarification_turn = :clarification_turn,
                    last_intent = :last_intent,
                    updated_at = NOW()
                WHERE session_id = :session_id
            """),
            {
                "session_id": session_id,
                "status": status,
                "pending_command": pending_command_json,
                "clarification_turn": clarification_turn,
                "last_intent": intent,
            },
        )
    else:
        db.execute(
            text("""
                INSERT INTO dialogue_sessions (
                    session_id,
                    messages,
                    status,
                    pending_command,
                    clarification_turn,
                    last_intent,
                    created_at,
                    updated_at
                )
                VALUES (
                    :session_id,
                    :messages,
                    :status,
                    :pending_command,
                    :clarification_turn,
                    :last_intent,
                    NOW(),
                    NOW()
                )
            """),
            {
                "session_id": session_id,
                "messages": json.dumps([], ensure_ascii=False),
                "status": status,
                "pending_command": pending_command_json,
                "clarification_turn": clarification_turn,
                "last_intent": intent,
            },
        )

    db.commit()