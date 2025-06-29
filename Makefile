.PHONY: help install dev clean test lint type-check format check run all

# Variables
PYTHON := python
UV := uv
SRC_DIR := src
TESTS_DIR := tests

help: ## Affiche cette aide
	@echo "Commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances de production
	$(UV) sync --no-dev

dev: ## Installe les dépendances de développement
	$(UV) sync

clean: ## Nettoie les fichiers temporaires
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

test: ## Lance les tests avec coverage
	$(PYTHON) -m pytest $(TESTS_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-quick: ## Lance les tests sans coverage
	$(PYTHON) -m pytest $(TESTS_DIR) -v

lint: ## Vérifie le code avec ruff
	$(PYTHON) -m ruff check $(SRC_DIR) $(TESTS_DIR)

lint-fix: ## Corrige automatiquement les erreurs de lint
	$(PYTHON) -m ruff check --fix $(SRC_DIR) $(TESTS_DIR)

type-check: ## Vérifie les types avec mypy
	$(PYTHON) -m mypy $(SRC_DIR)

format: ## Formate le code avec black
	$(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR)

format-check: ## Vérifie le formatage sans modifier
	$(PYTHON) -m black --check $(SRC_DIR) $(TESTS_DIR)

check: lint type-check format-check ## Lance toutes les vérifications (lint, types, format)

run: ## Lance l'application
	$(PYTHON) -m onlyfans_economic_index.main

all: clean dev check test ## Prépare l'environnement et lance toutes les vérifications

build: ## Construit le package
	$(UV) build

publish-test: build ## Publie sur TestPyPI
	$(UV) publish --repository testpypi

publish: build ## Publie sur PyPI
	$(UV) publish