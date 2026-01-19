from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from comment_service.api.deps import CurrentUserDep, OptionalUserDep, get_comment_service
from comment_service.dtos.http import CommentDto, CommentListResponse, CreateCommentRequest, CreateCommentResponse
from comment_service.services.comment_service import CommentAppService


post_router = APIRouter(prefix="/post", tags=["Post Comments"])
game_router = APIRouter(prefix="/game", tags=["Game Comments"])


@post_router.get("/comments/{entity_id}", response_model=CommentListResponse)
async def get_post_comments(
    entity_id: int,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    user: OptionalUserDep = None,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentListResponse:
    """Получить комментарии к посту"""
    user_id = user.get("user_id") if user else None
    return await comment_service.list_comments(
        entity_id=entity_id,
        entity_type="post",
        cursor=cursor,
        user_id=user_id,
    )


@game_router.get("/comments/{entity_id}", response_model=CommentListResponse)
async def get_game_comments(
    entity_id: int,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    user: OptionalUserDep = None,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentListResponse:
    """Получить комментарии к игре"""
    user_id = user.get("user_id") if user else None
    return await comment_service.list_comments(
        entity_id=entity_id,
        entity_type="game",
        cursor=cursor,
        user_id=user_id,
    )


@post_router.get("/comments/{comment_id}/children", response_model=CommentListResponse)
async def get_post_comment_children(
    comment_id: int,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    user: OptionalUserDep = None,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentListResponse:
    """Получить дочерние комментарии к комментарию поста"""
    user_id = user.get("user_id") if user else None
    return await comment_service.list_children(
        parent_id=comment_id,
        cursor=cursor,
        user_id=user_id,
    )


@game_router.get("/comments/{comment_id}/children", response_model=CommentListResponse)
async def get_game_comment_children(
    comment_id: int,
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    user: OptionalUserDep = None,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentListResponse:
    """Получить дочерние комментарии к комментарию игры"""
    user_id = user.get("user_id") if user else None
    return await comment_service.list_children(
        parent_id=comment_id,
        cursor=cursor,
        user_id=user_id,
    )


@post_router.post("/{entity_id}/comments", response_model=CreateCommentResponse)
async def create_post_comment(
    entity_id: int,
    request: CreateCommentRequest,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CreateCommentResponse:
    """Создать комментарий к посту (требует авторизации)"""
    comment = await comment_service.create_comment(
        entity_id=entity_id,
        entity_type="post",
        author_id=user["user_id"],
        author_username=user.get("username", ""),
        author_avatar=user.get("avatar"),
        text=request.text,
        parent_id=None,
    )
    return CreateCommentResponse(comment=comment)


@game_router.post("/{entity_id}/comments", response_model=CreateCommentResponse)
async def create_game_comment(
    entity_id: int,
    request: CreateCommentRequest,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CreateCommentResponse:
    """Создать комментарий к игре (требует авторизации)"""
    comment = await comment_service.create_comment(
        entity_id=entity_id,
        entity_type="game",
        author_id=user["user_id"],
        author_username=user.get("username", ""),
        author_avatar=user.get("avatar"),
        text=request.text,
        parent_id=None,
    )
    return CreateCommentResponse(comment=comment)


@post_router.post("/comments/{comment_id}/replies", response_model=CreateCommentResponse)
async def reply_to_post_comment(
    comment_id: int,
    request: CreateCommentRequest,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CreateCommentResponse:
    """Ответить на комментарий поста (требует авторизации)"""
    parent_comment = await comment_service.comment_repo.get_by_id(comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Parent comment not found")
    
    comment = await comment_service.create_comment(
        entity_id=parent_comment.entity_id,
        entity_type=parent_comment.entity_type,
        author_id=user["user_id"],
        author_username=user.get("username", ""),
        author_avatar=user.get("avatar"),
        text=request.text,
        parent_id=comment_id,
    )
    return CreateCommentResponse(comment=comment)


@game_router.post("/comments/{comment_id}/replies", response_model=CreateCommentResponse)
async def reply_to_game_comment(
    comment_id: int,
    request: CreateCommentRequest,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CreateCommentResponse:
    """Ответить на комментарий игры (требует авторизации)"""
    parent_comment = await comment_service.comment_repo.get_by_id(comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Parent comment not found")
    
    comment = await comment_service.create_comment(
        entity_id=parent_comment.entity_id,
        entity_type=parent_comment.entity_type,
        author_id=user["user_id"],
        author_username=user.get("username", ""),
        author_avatar=user.get("avatar"),
        text=request.text,
        parent_id=comment_id,
    )
    return CreateCommentResponse(comment=comment)


@post_router.post("/comments/{comment_id}/like", response_model=CommentDto)
async def like_post_comment(
    comment_id: int,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentDto:
    """Лайкнуть комментарий поста (требует авторизации)"""
    return await comment_service.set_reaction(comment_id=comment_id, user_id=user["user_id"], reaction="like")


@post_router.post("/comments/{comment_id}/dislike", response_model=CommentDto)
async def dislike_post_comment(
    comment_id: int,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentDto:
    """Дизлайкнуть комментарий поста (требует авторизации)"""
    return await comment_service.set_reaction(comment_id=comment_id, user_id=user["user_id"], reaction="dislike")


@game_router.post("/comments/{comment_id}/like", response_model=CommentDto)
async def like_game_comment(
    comment_id: int,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentDto:
    """Лайкнуть комментарий игры (требует авторизации)"""
    return await comment_service.set_reaction(comment_id=comment_id, user_id=user["user_id"], reaction="like")


@game_router.post("/comments/{comment_id}/dislike", response_model=CommentDto)
async def dislike_game_comment(
    comment_id: int,
    user: CurrentUserDep,
    comment_service: CommentAppService = Depends(get_comment_service),
) -> CommentDto:
    """Дизлайкнуть комментарий игры (требует авторизации)"""
    return await comment_service.set_reaction(comment_id=comment_id, user_id=user["user_id"], reaction="dislike")

