import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

# Загружаем переменные окружения из .env если есть (ДО импорта моделей)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from comment_service.repo.sql.models import Base

target_metadata = Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Получаем URL из переменных окружения или из alembic.ini
# Важно: загружаем после load_dotenv()
ALEMBIC_DATABASE_URL = os.getenv("ALEMBIC_DATABASE_URL")
ASYNC_URL = os.getenv("DATABASE_URL")

# Если DATABASE_URL не установлен, пытаемся использовать значение из alembic.ini
if not ASYNC_URL and not ALEMBIC_DATABASE_URL:
    sqlalchemy_url = config.get_main_option("sqlalchemy.url")
    if sqlalchemy_url:
        # Конвертируем синхронный URL в async для SQLite
        if sqlalchemy_url.startswith("sqlite:///"):
            ASYNC_URL = sqlalchemy_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            ALEMBIC_DATABASE_URL = sqlalchemy_url
        elif sqlalchemy_url.startswith("sqlite://"):
            ASYNC_URL = sqlalchemy_url.replace("sqlite://", "sqlite+aiosqlite://")
            ALEMBIC_DATABASE_URL = sqlalchemy_url
        else:
            # Для PostgreSQL и других БД используем синхронный URL для Alembic
            ALEMBIC_DATABASE_URL = sqlalchemy_url



def run_migrations_offline() -> None:
    url = ALEMBIC_DATABASE_URL or (ASYNC_URL and ASYNC_URL.replace("+asyncpg", ""))
    if not url:
        raise RuntimeError("Set ALEMBIC_DATABASE_URL or DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    if not ASYNC_URL:
        raise RuntimeError("Set DATABASE_URL for async migrations")
    connectable = create_async_engine(ASYNC_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    # Приоритет: ALEMBIC_DATABASE_URL > DATABASE_URL > alembic.ini
    if ALEMBIC_DATABASE_URL:
        # Используем синхронный URL напрямую
        synchronous_engine = create_engine(
            ALEMBIC_DATABASE_URL,
            poolclass=pool.NullPool,
        )
        with synchronous_engine.connect() as connection:
            do_run_migrations(connection)
        synchronous_engine.dispose()
    elif ASYNC_URL:
        # Если есть только async URL, используем async миграции
        asyncio.run(run_async_migrations())
    else:
        raise RuntimeError("Set DATABASE_URL or ALEMBIC_DATABASE_URL or configure sqlalchemy.url in alembic.ini")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

