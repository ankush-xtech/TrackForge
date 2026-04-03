# ═══════════════════════════════════════════════════════════
# WebWork Clone — Development Commands
# ═══════════════════════════════════════════════════════════

.PHONY: help dev up down logs migrate test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ──
up: ## Start all services
	docker compose up -d
	@echo "\n✅ Services started!"
	@echo "   API:      http://localhost:8000"
	@echo "   Docs:     http://localhost:8000/docs"
	@echo "   Frontend: http://localhost:3000"
	@echo "   MinIO:    http://localhost:9001"

down: ## Stop all services
	docker compose down

logs: ## View logs (all services)
	docker compose logs -f

logs-api: ## View API logs only
	docker compose logs -f api

logs-celery: ## View Celery worker logs
	docker compose logs -f celery-worker

rebuild: ## Rebuild and restart all services
	docker compose down
	docker compose build --no-cache
	docker compose up -d

# ── Database ──
migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="add users table")
	cd backend && alembic revision --autogenerate -m "$(msg)"

migrate-down: ## Rollback last migration
	cd backend && alembic downgrade -1

# ── Backend ──
api-dev: ## Run FastAPI dev server locally (without Docker)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

celery-dev: ## Run Celery worker locally
	cd backend && celery -A app.tasks.celery_app worker --loglevel=info

# ── Frontend ──
frontend-dev: ## Run Next.js dev server locally
	cd frontend && npm run dev

frontend-build: ## Build Next.js for production
	cd frontend && npm run build

# ── Testing ──
test: ## Run all tests
	cd backend && pytest tests/ -v
	cd frontend && npm run lint

test-api: ## Run backend tests only
	cd backend && pytest tests/ -v --cov=app

test-frontend: ## Run frontend lint and type check
	cd frontend && npm run lint && npx tsc --noEmit

# ── Linting ──
lint: ## Run linters
	cd backend && ruff check app/
	cd frontend && npm run lint

lint-fix: ## Fix linting issues
	cd backend && ruff check app/ --fix
	cd frontend && npx next lint --fix

# ── Cleanup ──
clean: ## Remove all build artifacts and containers
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next frontend/node_modules
	rm -rf desktop-agent/dist desktop-agent/release desktop-agent/node_modules
