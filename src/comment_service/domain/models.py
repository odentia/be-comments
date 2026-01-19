from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class Author:
    id: int
    username: str
    avatar: str | None = None


@dataclass
class Comment:
    """Доменная модель комментария"""

    id: int
    entity_id: int  # ID поста или игры
    entity_type: Literal["post", "game"]
    author_id: int
    author_username: str
    author_avatar: str | None
    text: str
    parent_id: int | None  # None = корневой комментарий
    rating: int = 0  # сумма лайков/дизлайков
    is_positive: bool = True  # общий тон (больше лайков = True)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
