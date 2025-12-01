from __future__ import annotations

from typing import Literal, Optional

from comment_service.domain.models import Comment
from comment_service.domain.repositories import CommentRepository
from comment_service.dtos.http import AuthorDto, CommentDto, CommentListResponse
from comment_service.core.config import Settings


class CommentAppService:
    def __init__(self, comment_repo: CommentRepository, settings: Settings):
        self.comment_repo = comment_repo
        self.settings = settings

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

        items = []
        for comment in comments:
            children_count = await self.comment_repo.count_children(comment.id)
            is_liked = False
            is_disliked = False
            if user_id:
                reaction = await self.comment_repo.get_user_reaction(comment.id, user_id)
                is_liked = reaction == "like"
                is_disliked = reaction == "dislike"

            items.append(
                CommentDto(
                    id=comment.id,
                    author=AuthorDto(
                        id=comment.author_id,
                        name=comment.author_name,
                        avatar=comment.author_avatar,
                    ),
                    date=comment.created_at,
                    text=comment.text,
                    isPositive=comment.is_positive,
                    rating=comment.rating,
                    parentId=comment.parent_id,
                    childrenCount=children_count,
                    isLikedMe=is_liked,
                    isDisLikedMe=is_disliked,
                    type=comment.entity_type,
                )
            )

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

        items = []
        for comment in comments:
            children_count = await self.comment_repo.count_children(comment.id)
            is_liked = False
            is_disliked = False
            if user_id:
                reaction = await self.comment_repo.get_user_reaction(comment.id, user_id)
                is_liked = reaction == "like"
                is_disliked = reaction == "dislike"

            items.append(
                CommentDto(
                    id=comment.id,
                    author=AuthorDto(
                        id=comment.author_id,
                        name=comment.author_name,
                        avatar=comment.author_avatar,
                    ),
                    date=comment.created_at,
                    text=comment.text,
                    isPositive=comment.is_positive,
                    rating=comment.rating,
                    parentId=comment.parent_id,
                    childrenCount=children_count,
                    isLikedMe=is_liked,
                    isDisLikedMe=is_disliked,
                    type=comment.entity_type,
                )
            )

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
        author_name: str,
        author_avatar: Optional[str],
        text: str,
        parent_id: Optional[int] = None,
    ) -> CommentDto:
        comment = Comment(
            id=0,  # будет установлен при сохранении
            entity_id=entity_id,
            entity_type=entity_type,
            author_id=author_id,
            author_name=author_name,
            author_avatar=author_avatar,
            text=text,
            parent_id=parent_id,
            rating=0,
            is_positive=True,
        )

        saved = await self.comment_repo.create(comment)
        children_count = await self.comment_repo.count_children(saved.id)

        return CommentDto(
            id=saved.id,
            author=AuthorDto(
                id=saved.author_id,
                name=saved.author_name,
                avatar=saved.author_avatar,
            ),
            date=saved.created_at,
            text=saved.text,
            isPositive=saved.is_positive,
            rating=saved.rating,
            parentId=saved.parent_id,
            childrenCount=children_count,
            isLikedMe=False,
            isDisLikedMe=False,
            type=saved.entity_type,
        )

