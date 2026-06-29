"""
Description: Article API. Thin handlers delegate to the service layer so
             business rules live in one place.

Author: qinzhenya
Created: 2026-06-29
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate
from app.services import article_service

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleRead])
def list_articles(db: Session = Depends(get_db)) -> list[ArticleRead]:
    return article_service.list_articles(db)


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
def create_article(payload: ArticleCreate, db: Session = Depends(get_db)) -> ArticleRead:
    return article_service.create_article(db, payload)


@router.get("/{article_id}", response_model=ArticleRead)
def get_article(article_id: int, db: Session = Depends(get_db)) -> ArticleRead:
    return article_service.get_article(db, article_id)


@router.patch("/{article_id}", response_model=ArticleRead)
def update_article(
    article_id: int, payload: ArticleUpdate, db: Session = Depends(get_db)
) -> ArticleRead:
    return article_service.update_article(db, article_id, payload)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article(article_id: int, db: Session = Depends(get_db)) -> None:
    article_service.delete_article(db, article_id)
