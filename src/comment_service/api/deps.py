from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from comment_service.core.config import Settings
from comment_service.core.db import get_session_factory
from comment_service.repo.sql.repositories import SQLCommentRepository
from comment_service.services.comment_service import CommentAppService
from comment_service.mq.publisher import EventPublisher


bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    session_factory = getattr(request.app.state, "session_factory", None)
    if not session_factory:
        session_factory = get_session_factory()
    if not session_factory:
        raise RuntimeError("Session factory is not initialized")
    return session_factory


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = _get_session_factory(request)
    async with session_factory() as session:
        yield session


def get_comment_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SQLCommentRepository:
    return SQLCommentRepository(session)


def get_event_publisher(request: Request) -> EventPublisher | None:
    """Получить event publisher из app state"""
    return getattr(request.app.state, "event_publisher", None)


def get_comment_service(
    comment_repo: Annotated[SQLCommentRepository, Depends(get_comment_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
    event_publisher: Annotated[EventPublisher | None, Depends(get_event_publisher)] = None,
) -> CommentAppService:
    return CommentAppService(
        comment_repo=comment_repo,
        settings=settings,
        event_publisher=event_publisher,
    )


async def get_current_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    return "" if creds is None else creds.credentials


async def require_authenticated_user(
    token: Annotated[str, Depends(get_current_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Проверка аутентификации пользователя"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        username = payload.get("username") or payload.get("name", "")
        return {
            "user_id": int(user_id),
            "email": payload.get("email"),
            "username": username,
            "avatar": payload.get("avatar"),
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


CurrentUserDep = Annotated[dict, Depends(require_authenticated_user)]


async def get_optional_user(
    token: Annotated[str, Depends(get_current_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict | None:
    """Опциональная проверка аутентификации пользователя (для GET эндпоинтов)"""
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        username = payload.get("username") or payload.get("name", "")
        return {
            "user_id": int(user_id),
            "email": payload.get("email"),
            "username": username,
            "avatar": payload.get("avatar"),
        }
    except JWTError:
        return None


OptionalUserDep = Annotated[dict | None, Depends(get_optional_user)]
