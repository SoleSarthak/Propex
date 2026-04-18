.PHONY: setup dev test lint type-check migrate db-seed docker-build docker-up docker-down

# Developer commands
setup:
	@echo "Setting up development environment..."
	@powershell ./scripts/setup-dev.ps1

dev:
	@echo "Starting development environment..."
	@docker compose up -d

test:
	@echo "Running tests..."
	@pytest

lint:
	@echo "Running linters..."
	@flake8 .
	@black --check .

type-check:
	@echo "Running type checks..."
	@mypy .

# Database
migrate:
	@echo "Running migrations..."
	@cd migrations && alembic upgrade head

db-seed:
	@echo "Seeding database..."
	@python scripts/seed-db.py

# Docker
docker-build:
	@docker compose build

docker-up:
	@docker compose up -d

docker-down:
	@docker compose down
