from pydantic import BaseModel, Field, model_validator
from typing import Optional

# 엣지 -> 백엔드 (Request)
class CommandRequest(BaseModel):
    session_id: str | None = None
    device_id: str
    raw_text: str | None = None
    stt_text: str | None = None
    source: str | None = "edge"

    @model_validator(mode="after")
    def validate_text(self):
        if not self.raw_text and not self.stt_text:
            raise ValueError("raw_text 또는 stt_text 중 하나는 필요합니다.")

        if not self.raw_text and self.stt_text:
            self.raw_text = self.stt_text

        return self

# 백엔드 -> 엣지 (Response)
class CommandResponse(BaseModel):
    session_id: str = Field(..., example="sess-x9y8z7")
    clarification_needed: bool = Field(..., description="재질문 필요 여부")
    clarification_turn: int = Field(..., description="재질문 횟수")
    response_text: str = Field(..., description="TTS로 출력될 안내 문장")


# 엣지 -> 백엔드 (재질문 답변 요청)
class ClarifyRequest(BaseModel):
    device_id: str = Field(..., example="edge-pi-01")
    session_id: str = Field(..., example="sess-x9y8z7")
    user_answer: str = Field(..., example="거실이랑 주방만 해줘")
    clarification_turn: int = Field(..., example=1)
    pending_command: Optional[dict] = Field(None, description="이전 재질문에서 저장된 대기 명령")

# 백엔드 -> 엣지 (재질문/최종 응답) - 기존 CommandResponse와 규격이 같으므로 재사용하거나 명시적으로 정의
class ClarifyResponse(BaseModel):
    session_id: str
    clarification_needed: bool
    clarification_turn: int
    response_text: str
