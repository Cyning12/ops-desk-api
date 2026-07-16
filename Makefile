.PHONY: dev install sync lint test migrate revision clean

# Default target
dev:
	uv sync --extra dev
	uv run uvicorn app.main:app --reload --port 8000

# First-time setup
install:
	uv venv
	uv sync --extra dev

# Sync dependencies (auto-update when pyproject.toml changes)
sync:
	uv sync --extra dev

# Code quality
lint:
	uv run ruff check app tests

# Tests
test:
	uv run pytest tests

# Database migrations
migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(msg)"

# Clean build artifacts
clean:
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
