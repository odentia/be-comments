from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class CommentModel(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    entity_type: Mapped[Literal["post", "game"]] = mapped_column(
        String(10), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    author_username: Mapped[str] = mapped_column(String(255), nullable=False)
    author_avatar: Mapped[str | None] = mapped_column(String(512))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_positive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    parent: Mapped["CommentModel | None"] = relationship(
        "CommentModel", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["CommentModel"]] = relationship(
        "CommentModel", back_populates="parent", cascade="all, delete-orphan"
    )
    reactions: Mapped[list["CommentReactionModel"]] = relationship(
        "CommentReactionModel", back_populates="comment", cascade="all, delete-orphan"
    )


class CommentReactionModel(Base):
    __tablename__ = "comment_reactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reaction: Mapped[Literal["like", "dislike"]] = mapped_column(String(10), nullable=False)

    comment: Mapped[CommentModel] = relationship(back_populates="reactions")
