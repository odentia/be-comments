FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install uv
RUN uv pip install -e .

COPY . .

EXPOSE 8011

CMD ["uv", "run", "python", "-m", "comment_service.api"]

