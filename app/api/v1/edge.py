from fastapi import APIRouter
from fastapi import APIRouter

import httpx
from fastapi import HTTPException

from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.database import get_db
from app.ai_mcp.parser import parse_natural_language
from app.ai_mcp.clarifier import clarify_natural_language

# ✨ Clarify 관련 DTO들도 함께 import 해주어야 합니다.
from app.schemas.edge_dto import (
    CommandRequest, 
    CommandResponse, 
    ClarifyRequest, 
    ClarifyResponse
)

# 스프링의 @RequestMapping("/api/v1/commands")와 같은 역할
router = APIRouter(prefix="/api/v1", tags=["Edge Communication"])

# 1. 초기 명령 파싱
@router.post("/commands/parse")
async def parse_command(
    request: CommandRequest,
    db: Session = Depends(get_db),
):
    print(f"[/parse] Device: {request.device_id}, Text: {request.stt_text}")

    result = await parse_natural_language(
        raw_text=request.stt_text,
        session_id=getattr(request, "session_id", None),
        device_id=request.device_id,
        source="edge",
        db=db,
    )

    return result
    
# 2. 재질문 답변 처리 (추가된 부분)
@router.post("/dialogues/clarify")
async def clarify_dialogue(
    request: dict,
):
    result = await clarify_natural_language(
        session_id=request.get("session_id"),
        user_answer=request.get("user_answer"),
        pending_command=request.get("pending_command"),
    )

    return result

# @router.post("/dialogues/clarify-and-execute")
# async def clarify_and_execute_dialogue(request: dict):
#     try:
#         result = await request_clarify_and_execute_to_ai_mcp(request)
#         return result

#     except httpx.HTTPStatusError as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"AI/MCP Server returned error: {e.response.text}",
#         )

#     except httpx.HTTPError as e:
#         raise HTTPException(
#             status_code=502,
#             detail=f"AI/MCP Server connection failed: {str(e)}",
#         )



