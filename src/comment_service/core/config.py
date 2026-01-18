from __future__ import annotations

import os
import socket
from functools import lru_cache
from typing import Literal, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvName = Literal["dev", "test", "prod"]


class Settings(BaseSettings):
    app_name: str = Field(default="comment-service")
    app_version: str = Field(default="0.1.0")
    env: EnvName = Field(default="dev")
    enable_docs: bool = True
    alembic_database_url: str | None = None

    http_host: str = Field(default="0.0.0.0")
    http_port: int = Field(default=8011)
    reload: bool = Field(default=False)

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: str = Field(default="sqlite+aiosqlite:///./comments.db")
    sql_echo: bool = Field(default=False)

    # --- RabbitMQ ---
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        description="RabbitMQ connection URL",
    )

    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")

    public_base_url: Optional[AnyHttpUrl] = None
    hostname: str = Field(default_factory=socket.gethostname)

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    @classmethod
    def from_toml(cls, path: str) -> "Settings":
        with open(path, "rb") as fp:
            data = tomllib.load(fp)
        flat: dict[str, object] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat[sub_key] = sub_value
            else:
                flat[key] = value
        return cls(**flat)


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["*"]
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def load_settings() -> Settings:
    config_file = os.getenv("CONFIG_FILE") or os.getenv("APP_CONFIG")
    defaults = Settings()
    if config_file and os.path.exists(config_file):
        file_settings = Settings.from_toml(config_file)
        merged = file_settings.model_copy(update=defaults.model_dump(exclude_unset=True))
        merged.cors_allow_origins = _parse_origins(
            os.getenv("CORS_ALLOW_ORIGINS") or ",".join(file_settings.cors_allow_origins)
        )
        return merged

    defaults.cors_allow_origins = _parse_origins(os.getenv("CORS_ALLOW_ORIGINS"))
    return defaults

