.PHONY: install dev init-db migrate run test lint

install:
	uv sync

dev:
	uv sync --extra dev

init-db:
	uv run python -m db.init_db

migrate:
	uv run alembic upgrade head

run:
	uv run streamlit run app/main.py

test:
	uv run pytest -q

lint:
	uv run ruff check .
