# Sendero del Inmortal — atajos de desarrollo (Linux / macOS / WSL / Git Bash)
# Windows nativo: make.bat (mismos targets).

PY      := python/.venv/bin/python
PIP     := python/.venv/bin/pip
RUFF    := python/.venv/bin/ruff
PORT    ?= 8765

.DEFAULT_GOAL := help
.PHONY: help install venv backend test lint fixtures front-install front front-build test-front test-all clean

help: ## Lista de targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Crea el venv de Python si no existe
	@test -x $(PY) || python3 -m venv python/.venv
	@$(PIP) install -q -r python/requirements.txt

install: venv ## Instala dependencias
	@echo "Instalado. Ejecuta: make backend"

backend: venv ## Arranca la API en :$(PORT)
	@cd python && PORT=$(PORT) $(abspath $(PY)) -m app.main

test: venv ## Tests del backend (pytest)
	@cd python && $(abspath $(PY)) -m pytest tests/ -q

lint: venv ## Lint del backend (ruff)
	@$(RUFF) check python/app python/tests

fixtures: ## Regenera fixtures de paridad desde el monolito JS (requiere node)
	@node tools/gen_rng_fixture.mjs
	@node tools/gen_cards_fixture.mjs
	@node tools/gen_enemies_fixture.mjs

front-install: ## Instala dependencias del front (web/, npm)
	@cd web && npm install

front: ## Arranca el front en :5173 (el backend debe estar en :$(PORT))
	@cd web && npm run dev

front-build: ## Build de producción del front (tsc + vite)
	@cd web && npm run build

test-front: ## Tests del front (vitest)
	@cd web && npm run test

test-all: test test-front ## Todos los tests (back + front)

clean: ## Borra caches
	@find python -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf python/.pytest_cache
	@echo "Limpio."
