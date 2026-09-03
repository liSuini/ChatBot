from fastapi import APIRouter

from app.api.v1 import auth, conversations, llm, messages

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(llm.router)
api_router.include_router(messages.router)
