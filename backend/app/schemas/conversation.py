from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=200)
    # None → 使用默认 provider（settings.default_llm_provider）
    model_provider: str | None = Field(default=None, max_length=50)


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    tokens: int
    parent_message_id: int | None
    created_at: datetime


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    model_provider: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[MessageOut] = []
