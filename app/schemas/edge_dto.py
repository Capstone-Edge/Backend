from pydantic import BaseModel, model_validator


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
