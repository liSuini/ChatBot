"""文档相关 Pydantic 响应模型"""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
