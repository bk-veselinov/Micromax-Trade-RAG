.PHONY: up down extract ingest test eval lint

up:
	docker compose up -d --build

down:
	docker compose down

extract:
	uv run python -m app.ingestion.extract

ingest:
	docker compose run --rm api python -m app.ingestion.ingest

test:
	uv run pytest -q

eval:
	uv run python eval/run_eval.py

lint:
	uv run ruff check .