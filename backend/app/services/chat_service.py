from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.llm.factory import get_provider
from app.models.conversation import Conversation


class ChatService:
    """会话与消息领域服务（T04 会话部分；消息/SSE 部分在 T05 扩展）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 会话 ----------

    async def create_conversation(
        self, user_id: int, title: str, model_provider: str | None
    ) -> Conversation:
        provider_name = model_provider or settings.default_llm_provider
        get_provider(provider_name)  # 校验 provider 存在，未知抛 400
        conv = Conversation(user_id=user_id, title=title, model_provider=provider_name)
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def list_conversations(self, user_id: int) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        )
        return list(result.scalars().all())

    async def get_conversation_detail(self, user_id: int, conversation_id: int) -> Conversation:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundError("会话不存在")
        return conv

    async def rename_conversation(
        self, user_id: int, conversation_id: int, title: str
    ) -> Conversation:
        conv = await self._get_owned(user_id, conversation_id)
        conv.title = title
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def delete_conversation(self, user_id: int, conversation_id: int) -> None:
        conv = await self._get_owned(user_id, conversation_id)
        await self.db.delete(conv)
        await self.db.commit()

    async def _get_owned(self, user_id: int, conversation_id: int) -> Conversation:
        """按 id 取当前用户的会话；不存在或不属于该用户一律 404（不泄露存在性）"""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundError("会话不存在")
        return conv
