from fastapi import APIRouter, Depends

from app.deps.auth import get_current_user
from app.llm.factory import get_available_providers
from app.models.user import User

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/providers")
async def list_providers(user: User = Depends(get_current_user)):
    """返回当前配置下可用的 LLM Provider 列表（前端模型选择器用）"""
    return get_available_providers()
