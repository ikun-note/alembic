"""
Description: Database engine and session factory wired to application settings.

Author: qinzhenya
Created: 2026-06-29
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session and ensure it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
