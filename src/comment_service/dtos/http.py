from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AuthorDto(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None


class CommentDto(BaseModel):
    id: int
    author: AuthorDto
    date: datetime
    text: str
    isPositive: bool
    rating: int
    parentId: Optional[int] = None
    childrenCount: int
    isLikedMe: bool
    isDisLikedMe: bool
    type: Literal["post", "game"]


class CommentListResponse(BaseModel):
    items: list[CommentDto]
    hasMore: bool
    nextCursor: Optional[str] = None


class CreateCommentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class CreateCommentResponse(BaseModel):
    comment: CommentDto

