.PHONY: help install install-dev test lint format clean build docs docs-serve docs-deploy

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	poetry install

install-dev: ## Install the package in development mode with dev dependencies
	poetry install --with dev

install-docs: ## Install documentation dependencies
	poetry install --with docs

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=slurm_cli --cov-report=xml --cov-report=term-missing

lint: ## Run linting checks
	poetry run flake8 --max-line-length=88 --extend-ignore=E203,W503,E501 src tests
	poetry run mypy src

format: ## Format code
	poetry run black --line-length=72 src tests
	poetry run isort --profile=black src tests

format-check: ## Check code formatting
	poetry run black --check src tests
	poetry run isort --check-only src tests

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf site/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

docs: install-docs ## Build documentation
	poetry run mkdocs build

docs-serve: install-docs ## Serve documentation locally
	poetry run mkdocs serve -a 0.0.0.0:$(if $(DOCS_PORT),$(DOCS_PORT),8080)

docs-deploy: install-docs ## Deploy documentation to GitHub Pages
	poetry run mkdocs gh-deploy

demo: ## Run the CLI tool
	poetry run slurm-cli --help

pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

tox: ## Run tox tests
	poetry run tox

check: format-check lint test ## Run all checks

shell: ## Start Poetry shell
	poetry shell

update: ## Update dependencies
	poetry update

lock: ## Update lock file
	poetry lock

show: ## Show package information
	poetry show

outdated: ## Show outdated dependencies
	poetry show --outdated
