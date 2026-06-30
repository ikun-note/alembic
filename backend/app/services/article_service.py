"""
Description: Article service. Basic CRUD wiring; richer rules are added here as
             the project grows.

Author: qinzhenya
Created: 2026-06-29
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate


def _get_or_404(db: Session, article_id: int) -> Article:
    article = db.get(Article, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article


def list_articles(db: Session) -> list[ArticleRead]:
    articles = db.scalars(select(Article).order_by(Article.id)).all()
    return [ArticleRead.model_validate(article) for article in articles]


def create_article(db: Session, payload: ArticleCreate) -> ArticleRead:
    article = Article(title=payload.title, content=payload.content, status=payload.status)
    db.add(article)
    db.commit()
    db.refresh(article)
    return ArticleRead.model_validate(article)


def get_article(db: Session, article_id: int) -> ArticleRead:
    return ArticleRead.model_validate(_get_or_404(db, article_id))


def update_article(db: Session, article_id: int, payload: ArticleUpdate) -> ArticleRead:
    article = _get_or_404(db, article_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return ArticleRead.model_validate(article)


def delete_article(db: Session, article_id: int) -> None:
    article = _get_or_404(db, article_id)
    db.delete(article)
    db.commit()
