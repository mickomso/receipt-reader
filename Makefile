# Receipt Reader — Makefile

PYTHON := /opt/homebrew/bin/python3.13
BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV := $(BACKEND_DIR)/.venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn

.PHONY: help install install-backend install-frontend \
        dev dev-backend dev-frontend \
        test test-backend test-frontend \
        lint lint-backend lint-frontend \
        build clean

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Instalación ────────────────────────────────────────────────────────────────

install: install-backend install-frontend  ## Instala todas las dependencias

install-backend:  ## Instala dependencias del backend
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e "$(BACKEND_DIR)[dev]"

install-frontend:  ## Instala dependencias del frontend
	cd $(FRONTEND_DIR) && npm install

# ── Desarrollo ─────────────────────────────────────────────────────────────────

dev-backend:  ## Arranca el backend en modo desarrollo (reload)
	@mkdir -p data/uploads
	@cp -n .env.example .env 2>/dev/null || true
	cd $(BACKEND_DIR) && ../$(UVICORN) app.main:app --reload \
	  --reload-include '*.env' \
	  --host 0.0.0.0 --port 8000

dev-frontend:  ## Arranca el frontend en modo desarrollo
	cd $(FRONTEND_DIR) && npm run dev

dev:  ## Arranca backend y frontend en paralelo (requiere make ≥ 4.3)
	$(MAKE) -j2 dev-backend dev-frontend

# ── Tests ──────────────────────────────────────────────────────────────────────

test: test-backend  ## Ejecuta todos los tests del backend

test-backend:  ## Ejecuta los tests de Pytest
	cd $(BACKEND_DIR) && ../$(PYTEST) tests/ -v --tb=short

test-backend-cov:  ## Tests con cobertura
	cd $(BACKEND_DIR) && ../$(PYTEST) tests/ --cov=app --cov-report=term-missing

test-frontend:  ## Ejecuta los tests E2E de Playwright
	cd $(FRONTEND_DIR) && npx playwright install --with-deps chromium && npm run test:e2e

# ── Lint ───────────────────────────────────────────────────────────────────────

lint-backend:  ## Linting del backend con Ruff
	cd $(BACKEND_DIR) && ../$(VENV)/bin/ruff check app/ tests/

lint-frontend:  ## Linting del frontend
	cd $(FRONTEND_DIR) && npm run check

lint: lint-backend lint-frontend  ## Lint completo

# ── Build ──────────────────────────────────────────────────────────────────────

build-frontend:  ## Build de producción del frontend
	cd $(FRONTEND_DIR) && npm run build

build: build-frontend  ## Build completo

# ── Limpieza ───────────────────────────────────────────────────────────────────

clean:  ## Elimina artefactos generados
	rm -rf $(VENV)
	rm -rf $(FRONTEND_DIR)/node_modules
	rm -rf $(FRONTEND_DIR)/.svelte-kit
	rm -rf $(BACKEND_DIR)/__pycache__
	find $(BACKEND_DIR) -name "*.pyc" -delete
	rm -f data/receipt_reader.db
	rm -f backend/test_receipt_reader.db
