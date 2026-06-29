"""
Description: Application settings. Merges CLI/ENV/CONFIG/DEFAULT into one object;
             secrets stay in ENV (.env), non-secret values in config.toml.

Author: qinzhenya
Created: 2026-06-29
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_file_encoding="utf-8",
        toml_file="config.toml",
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 5432
    user: str = "alembic_lab"
    name: str = "alembic_lab"
    # Required, ENV-only: no default means the app refuses to start without a password.
    password: SecretStr

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    @property
    def database_url(self) -> str:
        password = self.password.get_secret_value()
        return f"postgresql+psycopg://{self.user}:{password}@{self.host}:{self.port}/{self.name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
