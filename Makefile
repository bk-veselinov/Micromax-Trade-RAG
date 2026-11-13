# Phase 0. Targets from asd.md.
.PHONY: up down extract ingest test eval lint

up:
	# TODO: docker compose up -d --build
down:
	# TODO: docker compose down
extract:
	# TODO: uv run python -m app.ingestion.extract
ingest:
	# TODO: uv run python -m app.ingestion.ingest
test:
	# TODO: uv run pytest
eval:
	# TODO: uv run python eval/run_eval.py
lint:
	# TODO: uv run ruff check .
