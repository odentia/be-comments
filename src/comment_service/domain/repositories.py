from __future__ import annotations

from typing import List, Optional, Protocol, Tuple, Literal

from comment_service.domain.models import Comment


class CommentRepository(Protocol):
    """Репозиторий для работы с комментариями"""

    async def create(self, comment: Comment) -> Comment:
        ...

    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        ...

    async def list_root_comments(
        self,
        entity_id: int,
        entity_type: str,
        cursor: Optional[str] = None,
        limit: int = 5,
    ) -> Tuple[List[Comment], Optional[str]]:
        """
        Получить корневые комментарии с курсорной пагинацией.
        Возвращает (список комментариев, следующий курсор или None).
        """
        ...

    async def list_children(
        self,
        parent_id: int,
        cursor: Optional[str] = None,
        limit: int = 5,
    ) -> Tuple[List[Comment], Optional[str]]:
        """
        Получить дочерние комментарии с курсорной пагинацией.
        Возвращает (список комментариев, следующий курсор или None).
        """
        ...

    async def count_children(self, parent_id: int) -> int:
        """Подсчитать количество прямых дочерних комментариев"""
        ...

    async def update_rating(self, comment_id: int, rating: int, is_positive: bool) -> None:
        """Обновить рейтинг комментария"""
        ...

    async def get_user_reaction(self, comment_id: int, user_id: int) -> Optional[Literal["like", "dislike"]]:
        """Получить реакцию пользователя на комментарий (like/dislike или None)"""
        ...

    async def set_user_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: Optional[Literal["like", "dislike"]],
    ) -> None:
        """Установить реакцию пользователя (like/dislike или None для удаления)"""
        ...

