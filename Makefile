.PHONY: help install lint lint-fix format check clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	pip install -r requirements-dev.txt

lint: ## Run linting checks
	ruff check project/

lint-fix: ## Auto-fix linting issues
	ruff check --fix project/

format: ## Format code with black and isort
	ruff format project/
	ruff check --select I --fix project/

check: ## Run all checks (lint + format)
	ruff check project/
	ruff format --check project/
	ruff check --select I project/

clean: ## Clean up cache files
	find project/ -type d -name "__pycache__" -exec rm -rf {} +
	find project/ -type d -name "*.egg-info" -exec rm -rf {} +
	find project/ -type d -name ".ruff_cache" -exec rm -rf {} +
	find project/ -type f -name "*.pyc" -delete
