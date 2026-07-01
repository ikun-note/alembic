"""
Description: Article domain model. Exploration carrier that evolves across
             migrations (columns added, renamed, backfilled).

Author: qinzhenya
Created: 2026-06-29
"""

from datetime import datetime

from sqlalchemy import Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(String(), default="")
    status: Mapped[str] = mapped_column(Enum("draft", "published", "archived", name="article_status"), default="draft")
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"
