from fastapi import APIRouter

from app.ai_mcp.clarifier import clarify_natural_language
from app.schemas.edge_dto import ClarifyRequest, ClarifyResponse

router = APIRouter(prefix="/api/v1/dialogues", tags=["Dialogues"])


@router.post("/clarify")
async def clarify_dialogue(request: ClarifyRequest):
    result = await clarify_natural_language(
        session_id=request.session_id,
        user_answer=request.user_answer,
        pending_command=request.pending_command,
    )

    return result
