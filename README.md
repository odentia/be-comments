# comment-service

Микросервис для управления комментариями к постам и играм.

## Возможности

- Создание комментариев к постам и играм
- Иерархическая структура комментариев (ответы на комментарии)
- Курсорная пагинация (по 5 элементов)
- Лайки/дизлайки комментариев
- Авторизация через JWT токены

## Стек

- FastAPI, Uvicorn
- SQLAlchemy (async) + PostgreSQL/SQLite
- Alembic для миграций
- JWT для авторизации

## Запуск

```bash
uv sync
uv run alembic upgrade head
uv run python -m comment_service.api
```

## Переменные окружения (.env)

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/comments
ALEMBIC_DATABASE_URL=postgresql://user:pass@localhost:5432/comments
JWT_SECRET_KEY=<your key>
```

## API

### Получение комментариев

- `GET /api/v1/post/comments/{id}?cursor=...` — получить комментарии к посту
- `GET /api/v1/game/comments/{id}?cursor=...` — получить комментарии к игре
- `GET /api/v1/post/comments/{id}/children?cursor=...` — получить дочерние комментарии
- `GET /api/v1/game/comments/{id}/children?cursor=...` — получить дочерние комментарии

### Создание комментариев (требует авторизации)

- `POST /api/v1/post/{id}/comments` — создать комментарий к посту
- `POST /api/v1/game/{id}/comments` — создать комментарий к игре
- `POST /api/v1/post/comments/{id}/replies` — ответить на комментарий поста
- `POST /api/v1/game/comments/{id}/replies` — ответить на комментарий игры