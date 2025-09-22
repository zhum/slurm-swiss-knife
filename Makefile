.PHONY: help install install-dev test lint format clean build docs

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
	poetry run pytest --cov=slurm_cli --cov-report=html --cov-report=term-missing

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
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

docs: ## Build documentation
	poetry run sphinx-build -W -b html docs docs/_build/html

docs-serve: ## Serve documentation locally
	poetry run sphinx-autobuild docs docs/_build/html

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