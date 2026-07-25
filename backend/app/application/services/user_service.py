from datetime import datetime, timedelta
from typing import Optional
import uuid
import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from app.core.config import settings
from app.infrastructure.database.models import User, Role
from app.infrastructure.repositories.users import UserRepository
from app.schemas.user import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self.user_repo.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.user_repo.get_by_email(email)

    async def create_user(self, schema: UserCreate) -> User:
        # Check if user already exists
        existing = await self.get_by_email(schema.email)
        if existing:
            raise ValueError("Email already registered.")

        # Find or create role
        # For simplicity in Phase 1, we look up or seed the role
        session = self.user_repo.session
        role_query = select(Role).where(Role.name == schema.role_name)
        result = await session.execute(role_query)
        role = result.scalar_one_or_none()

        if not role:
            role = Role(name=schema.role_name, permissions={"all": True} if schema.role_name == "Admin" else {})
            session.add(role)
            await session.flush()

        hashed_password = pwd_context.hash(schema.password)
        new_user = User(
            email=schema.email,
            hashed_password=hashed_password,
            role_id=role.id,
            is_active=schema.is_active
        )
        await self.user_repo.add(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, user_id: uuid.UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": str(user_id), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[uuid.UUID]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id_str: str = payload.get("sub")
            if not user_id_str:
                return None
            return uuid.UUID(user_id_str)
        except (jwt.PyJWTError, ValueError):
            return None
