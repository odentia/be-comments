from __future__ import annotations

from comment_service.domain.models import Comment
from comment_service.repo.sql import models as m


def comment_to_domain(model: m.CommentModel) -> Comment:
    return Comment(
        id=model.id,
        entity_id=model.entity_id,
        entity_type=model.entity_type,
        author_id=model.author_id,
        author_username=model.author_username,
        author_avatar=model.author_avatar,
        text=model.text,
        parent_id=model.parent_id,
        rating=model.rating,
        is_positive=model.is_positive,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def comment_to_model(domain: Comment) -> m.CommentModel:
    return m.CommentModel(
        id=domain.id if domain.id > 0 else None,  # None для новых записей
        entity_id=domain.entity_id,
        entity_type=domain.entity_type,
        author_id=domain.author_id,
        author_username=domain.author_username,
        author_avatar=domain.author_avatar,
        text=domain.text,
        parent_id=domain.parent_id,
        rating=domain.rating,
        is_positive=domain.is_positive,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
