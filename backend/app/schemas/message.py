from pydantic import BaseModel, Field


class MessageSend(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    rag_enabled: bool = False
