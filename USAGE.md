# Инструкция по использованию comment-service

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Используя uv (рекомендуется)
uv sync

# Или через pip
pip install -e .
```

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# База данных
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/comments
# Или для SQLite (для разработки):
# DATABASE_URL=sqlite+aiosqlite:///./comments.db

# Для Alembic (синхронный драйвер)
ALEMBIC_DATABASE_URL=postgresql://user:password@localhost:5432/comments

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Приложение
APP_NAME=comment-service
LOG_LEVEL=INFO
HTTP_PORT=8011
```

### 3. Применение миграций

```bash
# Через Makefile
make migrate

# Или напрямую
uv run alembic upgrade head
```

### 4. Запуск сервиса

```bash
# Через Makefile
make run

# Или напрямую
uv run python -m comment_service.api
```

Сервис будет доступен по адресу: `http://localhost:8011`

---

## 📚 API Документация

После запуска сервиса доступна интерактивная документация:
- Swagger UI: `http://localhost:8011/docs`
- ReDoc: `http://localhost:8011/redoc`
- OpenAPI JSON: `http://localhost:8011/openapi.json`

---

## 🔌 Использование API

### Базовый URL

```
http://localhost:8011/api/v1
```

### Получение комментариев к посту

```bash
# Первая страница
curl "http://localhost:8011/api/v1/post/comments/123"

# Следующая страница (если есть nextCursor)
curl "http://localhost:8011/api/v1/post/comments/123?cursor=eyJpZCI6MTIzfQ=="
```

**Ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "author": {
        "id": 10,
        "name": "vasya",
        "avatar": null
      },
      "date": "2025-11-27T15:12:00.000Z",
      "text": "крутой пост",
      "isPositive": true,
      "rating": 5,
      "parentId": null,
      "childrenCount": 2,
      "isLikedMe": false,
      "isDisLikedMe": false,
      "type": "post"
    }
  ],
  "hasMore": true,
  "nextCursor": "eyJpZCI6MTI1fQ=="
}
```

### Получение комментариев к игре

```bash
curl "http://localhost:8011/api/v1/game/comments/456"
```

### Получение дочерних комментариев

```bash
# Дочерние комментарии для комментария с ID=42
curl "http://localhost:8011/api/v1/post/comments/42/children?cursor=eyJpZCI6MTIzfQ=="
```

### Создание комментария к посту

**Требуется авторизация!**

```bash
# Создать JWT токен (пример)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Создать комментарий
curl -X POST "http://localhost:8011/api/v1/post/123/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "очень годный пост"}'
```

**Ответ:**
```json
{
  "comment": {
    "id": 124,
    "author": {
      "id": 10,
      "name": "vasya",
      "avatar": null
    },
    "date": "2025-11-27T16:00:00.000Z",
    "text": "очень годный пост",
    "isPositive": true,
    "rating": 0,
    "parentId": null,
    "childrenCount": 0,
    "isLikedMe": false,
    "isDisLikedMe": false,
    "type": "post"
  }
}
```

### Создание комментария к игре

```bash
curl -X POST "http://localhost:8011/api/v1/game/456/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "отличная игра"}'
```

### Ответ на комментарий

```bash
# Ответить на комментарий с ID=42
curl -X POST "http://localhost:8011/api/v1/post/comments/42/replies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "согласен!"}'
```

---

## 🔐 Авторизация

### Формат JWT токена

Токен должен содержать следующие поля в payload:

```json
{
  "sub": "123",           // user_id (обязательно)
  "email": "user@example.com",
  "name": "User Name",
  "avatar": "https://example.com/avatar.jpg"
}
```

### Генерация тестового токена

Для разработки можно использовать скрипт:

```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

payload = {
    "sub": "123",  # user_id
    "email": "test@example.com",
    "name": "Test User",
    "avatar": None,
    "exp": datetime.utcnow() + timedelta(days=1)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Через Makefile
make test

# Или напрямую
uv run pytest
```

### Линтинг и форматирование

```bash
# Проверка кода
make lint

# Форматирование
make format
```

---

## 🐳 Docker

### Сборка образа

```bash
docker build -t comment-service:latest -f infra/docker/Dockerfile .
```

### Запуск контейнера

```bash
docker run -p 8011:8011 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/comments \
  -e JWT_SECRET_KEY=your-secret-key \
  comment-service:latest
```

---

## 📊 Мониторинг

### Health check

```bash
curl http://localhost:8011/api/v1/healthz
```

**Ответ:**
```json
{
  "status": "ok"
}
```

---

## 🔍 Отладка

### Логи

Логи выводятся в формате JSON (если настроено) или в стандартном формате.

Уровень логирования настраивается через переменную окружения:
```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### SQL запросы

Для отладки SQL запросов включите эхо:
```env
SQL_ECHO=true
```

---

## ⚙️ Конфигурация через TOML

Альтернативно можно использовать TOML файл:

```toml
# config.toml
[app]
name = "comment-service"
version = "0.1.0"
env = "dev"

[http]
host = "0.0.0.0"
port = 8011

[database]
url = "postgresql+asyncpg://user:pass@localhost:5432/comments"
```

Запуск с конфигом:
```bash
CONFIG_FILE=config.toml uv run python -m comment_service.api
```

---

## 🚨 Частые проблемы

### Ошибка подключения к БД

```
sqlalchemy.exc.OperationalError: ...
```

**Решение:** Проверьте `DATABASE_URL` и убедитесь, что база данных запущена.

### Ошибка авторизации

```
401 Unauthorized: Missing bearer token
```

**Решение:** Убедитесь, что токен передается в заголовке `Authorization: Bearer <token>`.

### Ошибка миграций

```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Решение:** Выполните `alembic upgrade head`.

---

## 📝 Примеры использования с разными клиентами

### Python (httpx)

```python
import httpx

BASE_URL = "http://localhost:8011/api/v1"
TOKEN = "your-jwt-token"

# Получить комментарии
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{BASE_URL}/post/comments/123",
        headers={"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    )
    data = response.json()
    print(data["items"])

# Создать комментарий
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{BASE_URL}/post/123/comments",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"text": "Отличный пост!"}
    )
    comment = response.json()["comment"]
    print(f"Создан комментарий: {comment['id']}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = "http://localhost:8011/api/v1";
const TOKEN = "your-jwt-token";

// Получить комментарии
async function getComments(postId, cursor = null) {
  const url = new URL(`${BASE_URL}/post/comments/${postId}`);
  if (cursor) url.searchParams.set("cursor", cursor);
  
  const response = await fetch(url, {
    headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}
  });
  return await response.json();
}

// Создать комментарий
async function createComment(postId, text) {
  const response = await fetch(`${BASE_URL}/post/${postId}/comments`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${TOKEN}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });
  return await response.json();
}
```

---

## 🔗 Интеграция с API Gateway

Если используется API Gateway (nginx/traefik), настройте роутинг:

```nginx
# nginx.conf
location /post/comments/ {
    proxy_pass http://comment-service:8011/api/v1/post/comments/;
}

location /game/comments/ {
    proxy_pass http://comment-service:8011/api/v1/game/comments/;
}
```

Таким образом, клиенты будут обращаться к `/post/comments/123`, а Gateway перенаправит на `/api/v1/post/comments/123`.

