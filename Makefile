.PHONY: dev migrate seed test scrape-all deploy-backend deploy-frontend logs db-shell db-reset db-backup

# ── Desarrollo ────────────────────────────────────────────────────────────────
dev:
	docker compose up --build

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Base de datos ─────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

migrate-down:
	cd backend && alembic downgrade -1

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

seed:
	cd backend && python -m app.scripts.seed_funders

db-shell:
	docker compose exec db psql -U postgres -d grantflow

db-reset:
	docker compose down -v && docker compose up -d db && sleep 3 && make migrate && make seed

db-backup:
	docker compose exec db pg_dump -U postgres grantflow > backup_$$(date +%Y%m%d_%H%M%S).sql

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	cd backend && python -m pytest tests/ -v

test-cov:
	cd backend && python -m pytest tests/ --cov=app --cov-report=html -v

# ── Scrapers ──────────────────────────────────────────────────────────────────
scrape-all:
	cd backend && python -m app.scrapers.runner

scrape:
	cd backend && python -m app.scrapers.runner --source $(SOURCE)

# ── Producción ────────────────────────────────────────────────────────────────
deploy-backend:
	@echo "Deploy backend a VPS..."
	git push origin main

deploy-frontend:
	@echo "Deploy frontend a Vercel..."
	cd frontend && npx vercel --prod

logs:
	docker compose logs -f backend
