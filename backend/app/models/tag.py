"""
Description: Tag model. Belongs to an Article (FK); exercises FK + index +
             naming_convention (stable constraint / index names).

Author: qinzhenya
Created: 2026-06-30
"""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK + 索引: 验 naming_convention 出来的 fk / ix 名
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    name: Mapped[str] = mapped_column(String(50))

    def __repr__(self) -> str:
        return f"<Tag id={self.id} article_id={self.article_id} name={self.name!r}>"
