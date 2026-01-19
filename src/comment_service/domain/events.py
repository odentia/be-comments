from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional


class CommentEvent(BaseModel):
    """Базовое событие комментария"""

    event_type: str
    timestamp: datetime = datetime.utcnow()
    service: str = "comment-service"


class CommentCreatedEvent(CommentEvent):
    """Событие создания комментария"""

    event_type: str = "comment_created"
    comment_id: int
    entity_id: int
    entity_type: Literal["post", "game"]
    author_id: int
    author_username: str
    parent_id: Optional[int] = None


class CommentDeletedEvent(CommentEvent):
    """Событие удаления комментария"""

    event_type: str = "comment_deleted"
    comment_id: int
    entity_id: int
    entity_type: Literal["post", "game"]


class CommentCountUpdatedEvent(CommentEvent):
    """Событие обновления количества комментариев (для синхронизации с post_service)"""

    event_type: str = "comment_count_updated"
    entity_id: int
    entity_type: Literal["post", "game"]
    comment_count: int
