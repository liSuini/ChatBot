from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ChatBotException
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, username: str, password: str) -> dict:
        result = await self.db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            raise ChatBotException("USERNAME_EXISTS", "用户名已被占用", 409)

        user = User(username=username, password_hash=hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return {
            "access_token": create_access_token(user.id),
            "refresh_token": None,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username},
        }

    async def login(self, username: str, password: str) -> dict:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        # 用户不存在与密码错误返回相同信息，避免用户名枚举
        if not user or not verify_password(password, user.password_hash):
            raise ChatBotException("INVALID_CREDENTIALS", "用户名或密码错误", 401)

        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username},
        }
