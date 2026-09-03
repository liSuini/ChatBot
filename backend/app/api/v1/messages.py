"""T05: 消息发送 + SSE 流式回复 端点"""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps.auth import get_current_user
from app.llm.factory import get_provider
from app.llm.schemas import LLMMessage
from app.models.user import User
from app.schemas.message import MessageSend
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["messages"])


def _sse(event: str, data: dict) -> str:
    """格式化一条 SSE 事件（中文不转义）"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    payload: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息并以 SSE 流式返回 AI 回复"""
    service = ChatService(db)

    # 1. 保存用户消息（同时校验会话归属）
    user_msg = await service.save_user_message(user.id, conversation_id, payload.content)

    # 2. 构建上下文
    conv = await service._get_owned(user.id, conversation_id)
    context = await service.build_context(conversation_id)
    provider = get_provider(conv.model_provider)

    # 清除可能残留的取消标志
    service.clear_cancel(conversation_id)

    async def event_stream():
        accumulated = ""
        try:
            yield _sse("start", {"message_id": user_msg.id})

            async for token in provider.stream_chat(context):
                if service.is_cancelled(conversation_id):
                    break
                accumulated += token
                yield _sse("token", {"content": token})

            # 保存 AI 回复
            tokens = len(accumulated)
            ai_msg = await service.save_assistant_message(
                conversation_id, accumulated, tokens
            )
            yield _sse("done", {
                "message_id": ai_msg.id,
                "content": accumulated,
                "tokens": tokens,
            })
        except Exception as exc:
            # 尽量保存已有内容
            if accumulated:
                await service.save_assistant_message(
                    conversation_id, accumulated, len(accumulated)
                )
            yield _sse("error", {"message": str(exc)})
        finally:
            service.clear_cancel(conversation_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/{conversation_id}/stop")
async def stop_generation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """停止当前会话的 AI 生成"""
    service = ChatService(db)
    # 校验会话归属（不存在/非本人 → 404）
    await service._get_owned(user.id, conversation_id)
    service.request_cancel(conversation_id)
    return {"status": "stopped"}


@router.post("/{conversation_id}/messages/{message_id}/regenerate")
async def regenerate_message(
    conversation_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """重新生成 AI 回复：复用原 user 消息上下文，新 assistant parent 指向旧 assistant"""
    service = ChatService(db)
    old_msg = await service.get_message(user.id, conversation_id, message_id)
    if old_msg.role != "assistant":
        from app.core.exceptions import ChatBotException
        raise ChatBotException("BAD_REQUEST", "只能重新生成 AI 回复", 400)

    context = await service.build_context_before(conversation_id, message_id)
    conv = await service._get_owned(user.id, conversation_id)
    provider = get_provider(conv.model_provider)
    service.clear_cancel(conversation_id)

    async def event_stream():
        accumulated = ""
        try:
            yield _sse("start", {"message_id": message_id})
            async for token in provider.stream_chat(context):
                if service.is_cancelled(conversation_id):
                    break
                accumulated += token
                yield _sse("token", {"content": token})
            tokens = len(accumulated)
            new_msg = await service.save_assistant_message(
                conversation_id, accumulated, tokens, parent_message_id=message_id
            )
            yield _sse("done", {
                "message_id": new_msg.id, "content": accumulated, "tokens": tokens,
            })
        except Exception as exc:
            if accumulated:
                await service.save_assistant_message(
                    conversation_id, accumulated, len(accumulated), parent_message_id=message_id
                )
            yield _sse("error", {"message": str(exc)})
        finally:
            service.clear_cancel(conversation_id)

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/{conversation_id}/messages/{message_id}/edit")
async def edit_message(
    conversation_id: int,
    message_id: int,
    payload: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """编辑用户消息并重发：新 user 消息 parent 指向原 user，重新生成 AI 回复"""
    service = ChatService(db)
    old_msg = await service.get_message(user.id, conversation_id, message_id)
    if old_msg.role != "user":
        from app.core.exceptions import ChatBotException
        raise ChatBotException("BAD_REQUEST", "只能编辑用户消息", 400)

    # 创建新 user 消息（parent 指向原 user 消息）
    new_user_msg = await service.save_user_message_with_parent(
        user.id, conversation_id, payload.content, message_id
    )

    # 构建上下文：原消息之前的消息 + 新编辑的消息
    context = await service.build_context_before(conversation_id, message_id)
    context.append(LLMMessage(role="user", content=payload.content))

    conv = await service._get_owned(user.id, conversation_id)
    provider = get_provider(conv.model_provider)
    service.clear_cancel(conversation_id)

    async def event_stream():
        accumulated = ""
        try:
            yield _sse("start", {"message_id": new_user_msg.id})
            async for token in provider.stream_chat(context):
                if service.is_cancelled(conversation_id):
                    break
                accumulated += token
                yield _sse("token", {"content": token})
            tokens = len(accumulated)
            ai_msg = await service.save_assistant_message(conversation_id, accumulated, tokens)
            yield _sse("done", {
                "message_id": ai_msg.id, "content": accumulated, "tokens": tokens,
            })
        except Exception as exc:
            if accumulated:
                await service.save_assistant_message(conversation_id, accumulated, len(accumulated))
            yield _sse("error", {"message": str(exc)})
        finally:
            service.clear_cancel(conversation_id)

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
