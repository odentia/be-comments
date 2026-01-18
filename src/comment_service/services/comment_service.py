from __future__ import annotations

from typing import Literal, Optional

from comment_service.domain.models import Comment
from comment_service.domain.repositories import CommentRepository
from comment_service.dtos.http import AuthorDto, CommentDto, CommentListResponse
from comment_service.core.config import Settings
from comment_service.mq.publisher import EventPublisher
from comment_service.domain.events import CommentCreatedEvent, CommentCountUpdatedEvent


class CommentAppService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        settings: Settings,
        event_publisher: EventPublisher | None = None,
    ):
        self.comment_repo = comment_repo
        self.settings = settings
        self.event_publisher = event_publisher

    async def list_comments(
        self,
        entity_id: int,
        entity_type: Literal["post", "game"],
        cursor: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> CommentListResponse:
        comments, next_cursor = await self.comment_repo.list_root_comments(
            entity_id=entity_id,
            entity_type=entity_type,
            cursor=cursor,
            limit=5,
        )

        items = [await self._build_comment_dto(comment, user_id) for comment in comments]

        return CommentListResponse(
            items=items,
            hasMore=next_cursor is not None,
            nextCursor=next_cursor,
        )

    async def list_children(
        self,
        parent_id: int,
        cursor: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> CommentListResponse:
        comments, next_cursor = await self.comment_repo.list_children(
            parent_id=parent_id,
            cursor=cursor,
            limit=5,
        )

        items = [await self._build_comment_dto(comment, user_id) for comment in comments]

        return CommentListResponse(
            items=items,
            hasMore=next_cursor is not None,
            nextCursor=next_cursor,
        )

    async def create_comment(
        self,
        entity_id: int,
        entity_type: Literal["post", "game"],
        author_id: int,
        author_username: str,
        author_avatar: Optional[str],
        text: str,
        parent_id: Optional[int] = None,
    ) -> CommentDto:
        comment = Comment(
            id=0,  # будет установлен при сохранении
            entity_id=entity_id,
            entity_type=entity_type,
            author_id=author_id,
            author_username=author_username,
            author_avatar=author_avatar,
            text=text,
            parent_id=parent_id,
            rating=0,
            is_positive=True,
        )

        saved = await self.comment_repo.create(comment)
        
        # Публикуем событие создания комментария
        if self.event_publisher:
            try:
                await self.event_publisher.publish(
                    CommentCreatedEvent(
                        comment_id=saved.id,
                        entity_id=saved.entity_id,
                        entity_type=saved.entity_type,
                        author_id=saved.author_id,
                        author_username=saved.author_username,
                        parent_id=saved.parent_id,
                    )
                )
                
                # Подсчитываем и публикуем обновление счетчика комментариев
                comment_count = await self.comment_repo.count_by_entity(
                    entity_id=saved.entity_id,
                    entity_type=saved.entity_type
                )
                await self.event_publisher.publish(
                    CommentCountUpdatedEvent(
                        entity_id=saved.entity_id,
                        entity_type=saved.entity_type,
                        comment_count=comment_count,
                    )
                )
            except Exception as e:
                # Логируем ошибку, но не прерываем выполнение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to publish comment events: {e}")
        
        return await self._build_comment_dto(saved, user_id=None)

    async def set_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: Literal["like", "dislike"],
    ) -> CommentDto:
        """Поставить реакцию и вернуть обновленный комментарий"""
        await self.comment_repo.set_user_reaction(comment_id, user_id, reaction)
        updated = await self.comment_repo.get_by_id(comment_id)
        if not updated:
            raise ValueError("Comment not found after reaction update")
        return await self._build_comment_dto(updated, user_id=user_id)

    async def _build_comment_dto(self, comment: Comment, user_id: Optional[int]) -> CommentDto:
        children_count = await self.comment_repo.count_children(comment.id)
        is_liked = False
        is_disliked = False
        if user_id:
            reaction = await self.comment_repo.get_user_reaction(comment.id, user_id)
            is_liked = reaction == "like"
            is_disliked = reaction == "dislike"

        return CommentDto(
            id=comment.id,
            author=AuthorDto(
                id=comment.author_id,
                username=comment.author_username,
                avatar=comment.author_avatar,
            ),
            date=comment.created_at,
            text=comment.text,
            isPositive=comment.is_positive,
            rating=comment.rating,
            parentId=comment.parent_id,
            childrenCount=children_count,
            isLikedByMe=is_liked,
            isDislikedByMe=is_disliked,
            type=comment.entity_type,
        )

