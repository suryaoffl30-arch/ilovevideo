.PHONY: dev build up down migrate seed test clean

dev:
	docker-compose up --build

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	docker-compose exec db psql -U postgres -d officialdir -f /docker-entrypoint-initdb.d/0001_create_schema.sql

seed:
	docker-compose exec backend python scripts/seed.py

test:
	cd backend && pytest app/tests/ -v

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

logs:
	docker-compose logs -f

backend-shell:
	docker-compose exec backend /bin/bash

db-shell:
	docker-compose exec db psql -U postgres -d officialdir

harvest:
	docker-compose exec backend python -m app.harvest run_once
