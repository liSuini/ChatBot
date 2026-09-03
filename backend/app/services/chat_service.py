from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.llm.factory import get_provider
from app.llm.schemas import LLMMessage
from app.models.conversation import Conversation
from app.models.message import Message

# 模块级取消标志：{conversation_id: True}
_cancel_flags: dict[int, bool] = {}


class ChatService:
    """会话与消息领域服务"""

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

    # ---------- 消息 ----------

    async def save_user_message(
        self, user_id: int, conversation_id: int, content: str
    ) -> Message:
        """保存用户消息，返回 Message 实例"""
        await self._get_owned(user_id, conversation_id)
        msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            parent_message_id=None,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def build_context(self, conversation_id: int) -> list[LLMMessage]:
        """构建 LLM 上下文：system prompt + 最近 20 条消息"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one()
        messages_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(20)
        )
        msgs = list(reversed(messages_result.scalars().all()))
        context: list[LLMMessage] = []
        if conv.system_prompt:
            context.append(LLMMessage(role="system", content=conv.system_prompt))
        context.extend(LLMMessage(role=m.role, content=m.content) for m in msgs)
        return context

    async def save_assistant_message(
        self, conversation_id: int, content: str, tokens: int = 0,
        parent_message_id: int | None = None,
    ) -> Message:
        """保存 AI 回复消息"""
        msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            tokens=tokens,
            parent_message_id=parent_message_id,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def save_user_message_with_parent(
        self, user_id: int, conversation_id: int, content: str, parent_id: int
    ) -> Message:
        """编辑重发：保存新 user 消息，parent 指向原 user 消息"""
        await self._get_owned(user_id, conversation_id)
        msg = Message(
            conversation_id=conversation_id,
            role="user",
            content=content,
            parent_message_id=parent_id,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_message(self, user_id: int, conversation_id: int, message_id: int) -> Message:
        """获取消息，校验会话归属"""
        await self._get_owned(user_id, conversation_id)
        result = await self.db.execute(
            select(Message).where(
                Message.id == message_id,
                Message.conversation_id == conversation_id,
            )
        )
        msg = result.scalar_one_or_none()
        if not msg:
            raise NotFoundError("消息不存在")
        return msg

    async def build_context_before(self, conversation_id: int, before_id: int) -> list[LLMMessage]:
        """构建上下文：给定消息之前的所有消息（用于重新生成/编辑重发）"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one()
        messages_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.id < before_id)
            .order_by(Message.id.desc())
            .limit(20)
        )
        msgs = list(reversed(messages_result.scalars().all()))
        context: list[LLMMessage] = []
        if conv.system_prompt:
            context.append(LLMMessage(role="system", content=conv.system_prompt))
        context.extend(LLMMessage(role=m.role, content=m.content) for m in msgs)
        return context

    # ---------- 取消标志 ----------

    @staticmethod
    def request_cancel(conversation_id: int) -> None:
        _cancel_flags[conversation_id] = True

    @staticmethod
    def is_cancelled(conversation_id: int) -> bool:
        return _cancel_flags.get(conversation_id, False)

    @staticmethod
    def clear_cancel(conversation_id: int) -> None:
        _cancel_flags.pop(conversation_id, None)
