# Savepoint Analytics - saber-football common commands.

.DEFAULT_GOAL := help
SHELL := /bin/bash
SEASON ?= 2025

.PHONY: help setup sync ingest ingest-pbp ingest-schedules ingest-teams ingest-players \
        ingest-rosters ingest-participation ingest-snap-counts core identity analytics reconcile \
        dbt dbt-duckdb test lint fmt typecheck serve clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv + install all dependency groups
	uv sync --all-extras

sync: ## Install runtime deps only
	uv sync

ingest: ingest-pbp ingest-schedules ## Pull core nflverse raw tables for $(SEASON)

ingest-pbp: ## Pull nflverse play-by-play for $(SEASON)
	uv run python -m src.ingestion.nflverse pbp --season $(SEASON)

ingest-schedules: ## Pull nflverse schedules for $(SEASON)
	uv run python -m src.ingestion.nflverse schedules --season $(SEASON)

ingest-teams: ## Pull nflverse team metadata snapshot
	uv run python -m src.ingestion.nflverse teams

ingest-players: ## Pull nflverse player/ID bridge snapshot
	uv run python -m src.ingestion.nflverse players

ingest-rosters: ## Pull nflverse rosters for $(SEASON)
	uv run python -m src.ingestion.nflverse rosters --season $(SEASON)

ingest-participation: ## Pull nflverse participation for $(SEASON)
	uv run python -m src.ingestion.nflverse participation --season $(SEASON)

ingest-snap-counts: ## Pull nflverse/PFR snap counts for $(SEASON)
	uv run python -m src.ingestion.nflverse snap_counts --season $(SEASON)

core: ## Build dim_game, fact_play, and fact_team_game for $(SEASON)
	uv run python -m src.warehouse.core --season $(SEASON)

identity: ## Build dim_team, dim_player, ID bridge, player-game, and player-on-play tables
	uv run python -m src.warehouse.identity --season $(SEASON)

analytics: ## Build team efficiency/style analytics for $(SEASON)
	uv run python -m src.analytics.team_style --season $(SEASON)

reconcile: ## Reconcile core EPA/WPA aggregates against raw nflverse data for $(SEASON)
	uv run python -m src.quality.reconciliation --season $(SEASON)

dbt: ## Build dbt models against Postgres
	cd dbt && uv run dbt build --target postgres

dbt-duckdb: ## Build dbt models against DuckDB
	cd dbt && uv run dbt build --target duckdb

test: ## Run pytest
	uv run pytest

lint: ## Lint with ruff
	uv run ruff check src tests

fmt: ## Format with ruff
	uv run ruff format src tests

typecheck: ## Type-check with mypy
	uv run mypy src

serve: ## Launch the Streamlit team-style dashboard
	uv run streamlit run src/serving/app.py

clean: ## Remove caches and build artifacts
	rm -rf .ruff_cache .mypy_cache .pytest_cache **/__pycache__ dbt/target dbt/logs
