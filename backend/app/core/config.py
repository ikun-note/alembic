"""
Description: Application settings. Layers (high -> low): CLI > ENV (.env) > DEFAULT.
             All DB connection values live in .env; no separate config file.

Author: qinzhenya
Created: 2026-06-29
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "alembic_lab"
    db: str = "alembic_lab"
    # Required, ENV-only: no default means the app refuses to start without a password.
    password: SecretStr

    @property
    def database_url(self) -> str:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        ).render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
