SHELL := /bin/bash

.PHONY: dev dev-docker down refresh test

dev:
	bash ./scripts/dev.sh

dev-docker:
	docker compose up --build

down:
	bash ./scripts/down.sh

refresh:
	curl -fsSL -X POST http://localhost:8000/refresh

test:
	cd backend && ../.venv/bin/python -m pytest
	cd frontend && npm run build