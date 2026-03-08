.PHONY: up down test fmt lint

up:
	docker compose up --build -d

down:
	docker compose down

test:
	docker compose run --rm backend python -m pytest tests/

fmt:
	docker compose run --rm backend python -m ruff format app/ tests/

lint:
	docker compose run --rm backend python -m ruff check app/ tests/
