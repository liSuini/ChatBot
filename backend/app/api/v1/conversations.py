from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationRename,
    ConversationSummary,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationSummary)
async def create_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).create_conversation(
        user.id, payload.title, payload.model_provider
    )


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).list_conversations(user.id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).get_conversation_detail(user.id, conversation_id)


@router.patch("/{conversation_id}", response_model=ConversationSummary)
async def rename_conversation(
    conversation_id: int,
    payload: ConversationRename,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ChatService(db).rename_conversation(user.id, conversation_id, payload.title)


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await ChatService(db).delete_conversation(user.id, conversation_id)
