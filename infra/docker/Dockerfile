FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first
COPY pyproject.toml uv.lock README.md ./

# Copy all files needed for installation
COPY src/ ./src/
COPY alembic.ini ./

# Install dependencies to system Python
RUN uv pip install --system -e .

EXPOSE 8011

CMD ["uv", "run", "python", "-m", "comment_service.api"]

