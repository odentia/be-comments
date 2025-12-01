.PHONY: install migrate run test lint format

install:
	uv sync

migrate:
	uv run alembic upgrade head

run:
	uv run python -m comment_service.api

lint:
	uv run ruff check src

format:
	uv run ruff format src

test:
	uv run pytest

