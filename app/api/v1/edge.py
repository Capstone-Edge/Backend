from fastapi import APIRouter
from fastapi import APIRouter

import httpx
from fastapi import HTTPException

from app.services.ai_mcp_client import (
    request_parse_to_ai_mcp,
    request_clarify_to_ai_mcp,
    request_clarify_and_execute_to_ai_mcp,
)

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
async def parse_command(request: CommandRequest):
    print(f"[/parse] Device: {request.device_id}, Text: {request.stt_text}")

    payload = {
        "session_id": getattr(request, "session_id", None),
        "device_id": request.device_id,
        "raw_text": request.stt_text,
        "source": "edge",
    }

    try:
        result = await request_parse_to_ai_mcp(payload)
        return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server returned error: {e.response.text}",
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server connection failed: {str(e)}",
        )
    
# 2. 재질문 답변 처리 (추가된 부분)
@router.post("/dialogues/clarify")
async def clarify_dialogue(request: dict):
    try:
        result = await request_clarify_to_ai_mcp(request)
        return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server returned error: {e.response.text}",
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server connection failed: {str(e)}",
        )

@router.post("/dialogues/clarify-and-execute")
async def clarify_and_execute_dialogue(request: dict):
    try:
        result = await request_clarify_and_execute_to_ai_mcp(request)
        return result

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server returned error: {e.response.text}",
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI/MCP Server connection failed: {str(e)}",
        )



