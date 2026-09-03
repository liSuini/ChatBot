from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatResult(BaseModel):
    content: str
    tokens: int  # 输入+输出总 token（估算或取 usage）


class EmbedResult(BaseModel):
    embedding: list[float]


class EmbedBatchResult(BaseModel):
    embeddings: list[list[float]]
