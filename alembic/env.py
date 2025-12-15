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
    # Пытаемся загрузить .env с обработкой ошибок кодировки
    try:
        load_dotenv(encoding="utf-8")
    except (UnicodeDecodeError, Exception):
        # Если не удалось из-за кодировки, пробуем загрузить только переменные без комментариев
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            try:
                with open(env_path, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")
                # Фильтруем только строки с переменными
                lines = [line.strip() for line in content.split("\n") 
                        if line.strip() and not line.strip().startswith("#") and "=" in line.strip()]
                # Устанавливаем переменные напрямую
                for line in lines:
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
            except Exception:
                pass
except ImportError:
    pass

from comment_service.repo.sql.models import Base

target_metadata = Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Получаем URL из переменных окружения или из alembic.ini
# Важно: загружаем после load_dotenv()
# Очищаем URL от проблемных символов кодировки
def _clean_url(url: str | None) -> str | None:
    if not url:
        return None
    # Удаляем не-UTF-8 символы и лишние пробелы
    try:
        # Сначала пытаемся декодировать как UTF-8, игнорируя ошибки
        if isinstance(url, bytes):
            url = url.decode('utf-8', errors='ignore')
        # Удаляем не-UTF-8 символы
        cleaned = url.encode('utf-8', errors='ignore').decode('utf-8').strip()
        return cleaned
    except Exception:
        return url.strip() if url else None

_raw_alembic_url = os.getenv("ALEMBIC_DATABASE_URL")
_raw_async_url = os.getenv("DATABASE_URL")

ALEMBIC_DATABASE_URL = _clean_url(_raw_alembic_url)
ASYNC_URL = _clean_url(_raw_async_url)

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
    # Очищаем URL перед использованием
    clean_url = str(ASYNC_URL).encode('utf-8', errors='ignore').decode('utf-8')
    connectable = create_async_engine(clean_url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    # Приоритет: ALEMBIC_DATABASE_URL > DATABASE_URL > alembic.ini
    if ALEMBIC_DATABASE_URL:
        # Парсим URL и заменяем драйвер на psycopg3
        from urllib.parse import urlparse, unquote
        try:
            url_str = str(ALEMBIC_DATABASE_URL).encode('utf-8', errors='ignore').decode('utf-8')
            parsed = urlparse(url_str)
            
            # Если это PostgreSQL, используем psycopg3 вместо psycopg2
            if parsed.scheme in ('postgresql', 'postgresql+psycopg2'):
                # Заменяем на psycopg3
                clean_url = url_str.replace('postgresql+psycopg2://', 'postgresql+psycopg://').replace('postgresql://', 'postgresql+psycopg://')
            else:
                clean_url = url_str
        except Exception:
            # Если не удалось распарсить, используем как есть с заменой драйвера
            clean_url = str(ALEMBIC_DATABASE_URL).encode('utf-8', errors='ignore').decode('utf-8')
            if clean_url.startswith('postgresql://') and '+psycopg' not in clean_url:
                clean_url = clean_url.replace('postgresql://', 'postgresql+psycopg://')
        
        # Используем синхронный URL напрямую
        synchronous_engine = create_engine(
            clean_url,
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

