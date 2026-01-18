from __future__ import annotations

from typing import List, Literal, Optional, Tuple

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from comment_service.domain.models import Comment
from comment_service.domain.repositories import CommentRepository
from comment_service.domain.services import decode_cursor, encode_cursor
from comment_service.repo.sql import models as m
from comment_service.repo.sql import mappers


class SQLCommentRepository(CommentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, comment: Comment) -> Comment:
        model = mappers.comment_to_model(comment)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        await self.session.commit()
        return mappers.comment_to_domain(model)

    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        result = await self.session.execute(select(m.CommentModel).where(m.CommentModel.id == comment_id))
        model = result.scalars().first()
        return mappers.comment_to_domain(model) if model else None

    async def list_root_comments(
        self,
        entity_id: int,
        entity_type: str,
        cursor: Optional[str] = None,
        limit: int = 5,
    ) -> Tuple[List[Comment], Optional[str]]:
        query = select(m.CommentModel).where(
            and_(
                m.CommentModel.entity_id == entity_id,
                m.CommentModel.entity_type == entity_type,
                m.CommentModel.parent_id.is_(None),
            )
        ).order_by(m.CommentModel.created_at.asc())

        if cursor:
            cursor_id = decode_cursor(cursor)
            if cursor_id:
                query = query.where(m.CommentModel.id > cursor_id)

        query = query.limit(limit + 1)  # +1 чтобы проверить, есть ли еще
        result = await self.session.execute(query)
        models = result.scalars().all()

        comments = [mappers.comment_to_domain(model) for model in models[:limit]]
        next_cursor = None
        if len(models) > limit:
            next_cursor = encode_cursor(models[limit - 1].id)

        return comments, next_cursor

    async def list_children(
        self,
        parent_id: int,
        cursor: Optional[str] = None,
        limit: int = 5,
    ) -> Tuple[List[Comment], Optional[str]]:
        query = select(m.CommentModel).where(
            m.CommentModel.parent_id == parent_id
        ).order_by(m.CommentModel.created_at.asc())

        if cursor:
            cursor_id = decode_cursor(cursor)
            if cursor_id:
                query = query.where(m.CommentModel.id > cursor_id)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        models = result.scalars().all()

        comments = [mappers.comment_to_domain(model) for model in models[:limit]]
        next_cursor = None
        if len(models) > limit:
            next_cursor = encode_cursor(models[limit - 1].id)

        return comments, next_cursor

    async def count_children(self, parent_id: int) -> int:
        result = await self.session.execute(
            select(func.count(m.CommentModel.id)).where(m.CommentModel.parent_id == parent_id)
        )
        return result.scalar_one() or 0

    async def update_rating(self, comment_id: int, rating: int, is_positive: bool) -> None:
        result = await self.session.execute(
            select(m.CommentModel).where(m.CommentModel.id == comment_id)
        )
        model = result.scalars().first()
        if model:
            model.rating = rating
            model.is_positive = is_positive
            await self.session.commit()

    async def get_user_reaction(self, comment_id: int, user_id: int) -> Optional[Literal["like", "dislike"]]:
        result = await self.session.execute(
            select(m.CommentReactionModel).where(
                and_(
                    m.CommentReactionModel.comment_id == comment_id,
                    m.CommentReactionModel.user_id == user_id,
                )
            )
        )
        reaction = result.scalars().first()
        return reaction.reaction if reaction else None

    async def set_user_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: Optional[Literal["like", "dislike"]],
    ) -> None:
        # Удалить существующую реакцию
        stmt = delete(m.CommentReactionModel).where(
            and_(
                m.CommentReactionModel.comment_id == comment_id,
                m.CommentReactionModel.user_id == user_id,
            )
        )
        await self.session.execute(stmt)

        # Добавить новую, если указана
        if reaction:
            new_reaction = m.CommentReactionModel(
                comment_id=comment_id,
                user_id=user_id,
                reaction=reaction,
            )
            self.session.add(new_reaction)

        # Пересчитать рейтинг комментария
        like_count_result = await self.session.execute(
            select(func.count(m.CommentReactionModel.id)).where(
                and_(
                    m.CommentReactionModel.comment_id == comment_id,
                    m.CommentReactionModel.reaction == "like",
                )
            )
        )
        dislike_count_result = await self.session.execute(
            select(func.count(m.CommentReactionModel.id)).where(
                and_(
                    m.CommentReactionModel.comment_id == comment_id,
                    m.CommentReactionModel.reaction == "dislike",
                )
            )
        )
        like_count = like_count_result.scalar_one() or 0
        dislike_count = dislike_count_result.scalar_one() or 0
        rating = like_count - dislike_count
        is_positive = like_count >= dislike_count

        await self.update_rating(comment_id, rating, is_positive)
        await self.session.commit()

    async def count_by_entity(self, entity_id: int, entity_type: str) -> int:
        """Подсчитать количество комментариев к указанной сущности (включая дочерние)"""
        result = await self.session.execute(
            select(func.count(m.CommentModel.id)).where(
                and_(
                    m.CommentModel.entity_id == entity_id,
                    m.CommentModel.entity_type == entity_type
                )
            )
        )
        return result.scalar_one() or 0

    async def delete_by_entity(self, entity_id: int, entity_type: str) -> int:
        """Удалить все комментарии к указанной сущности. Возвращает количество удаленных комментариев."""
        # Сначала удаляем реакции к комментариям этой сущности
        subquery = select(m.CommentModel.id).where(
            and_(
                m.CommentModel.entity_id == entity_id,
                m.CommentModel.entity_type == entity_type
            )
        )
        
        stmt_reactions = delete(m.CommentReactionModel).where(
            m.CommentReactionModel.comment_id.in_(subquery)
        )
        await self.session.execute(stmt_reactions)
        
        # Затем удаляем сами комментарии
        stmt_comments = delete(m.CommentModel).where(
            and_(
                m.CommentModel.entity_id == entity_id,
                m.CommentModel.entity_type == entity_type
            )
        )
        result = await self.session.execute(stmt_comments)
        await self.session.commit()
        
        return result.rowcount