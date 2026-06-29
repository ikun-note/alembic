"""
Description: Article DTOs (create/update/read).

Author: qinzhenya
Created: 2026-06-29
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArticleBase(BaseModel):
    title: str
    body: str = ""


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class ArticleRead(ArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
