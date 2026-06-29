"""
Description: FastAPI application entry.

Author: qinzhenya
Created: 2026-06-29
"""

from fastapi import FastAPI

from app.api import articles

app = FastAPI(title="Alembic Lab API", version="0.1.0")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(articles.router, prefix="/api")
