from fastapi import APIRouter
from fastapi import APIRouter

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
@router.post("/commands/parse", response_model=CommandResponse)
async def parse_command(request: CommandRequest):
    print(f"[/parse] Device: {request.device_id}, Text: {request.stt_text}")
    return CommandResponse(
        session_id="sess-x9y8z7",
        clarification_needed=True,
        clarification_turn=1,
        response_text="에어컨을 켤까요? 원하시는 온도를 말씀해 주세요."
    )

# 2. 재질문 답변 처리 (추가된 부분)
@router.post("/dialogues/clarify", response_model=ClarifyResponse)
async def clarify_dialogue(request: ClarifyRequest):
    """
    사용자의 재질문 답변을 처리합니다.
    지금은 Mock 데이터로 '성공적인 종료' 상황을 반환합니다.
    """
    print(f"[/clarify] Session: {request.session_id}, Answer: {request.user_answer}, Turn: {request.clarification_turn}")
    
    # Mock 응답: 대화가 완료되어 기기 제어로 넘어가는 상황 (clarification_needed: False)
    return ClarifyResponse(
        session_id=request.session_id,
        clarification_needed=False,
        clarification_turn=request.clarification_turn,
        response_text="거실과 주방 청소를 시작할게요."
    )






