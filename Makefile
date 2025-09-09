.PHONY: help install install-dev test test-cov lint format type-check clean build publish pre-commit setup-dev run-example

# Default target
help: ## Show this help message
	@echo "Biosample Enricher - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Installation targets
install: ## Install the package
	~/.local/bin/uv pip install -e .

install-dev: ## Install the package with development dependencies
	~/.local/bin/uv pip install -e ".[dev]"

setup-dev: install-dev ## Setup development environment (install deps + pre-commit)
	~/.local/bin/uv run pre-commit install

# Testing targets
test: ## Run tests
	~/.local/bin/uv run pytest -v

test-cov: ## Run tests with coverage
	~/.local/bin/uv run pytest -v --cov=biosample_enricher --cov-report=term-missing --cov-report=html

test-fast: ## Run tests (exclude slow tests)
	~/.local/bin/uv run pytest -v -m "not slow"

test-integration: ## Run integration tests only
	~/.local/bin/uv run pytest -v -m "integration"

# Code quality targets
lint: ## Run linting checks
	~/.local/bin/uv run ruff check .

lint-fix: ## Run linting checks and fix issues
	~/.local/bin/uv run ruff check --fix .

format: ## Format code
	~/.local/bin/uv run ruff format .

format-check: ## Check code formatting
	~/.local/bin/uv run ruff format --check .

type-check: ## Run type checking
	~/.local/bin/uv run mypy biosample_enricher/

# Combined quality checks
check: lint format-check type-check ## Run all code quality checks

check-fix: lint-fix format ## Run linting fixes and formatting

# Build and publish
build: clean ## Build distribution packages
	~/.local/bin/uv build

publish-test: build ## Publish to test PyPI
	~/.local/bin/uv publish --repository testpypi

publish: build ## Publish to PyPI
	~/.local/bin/uv publish

# Utility targets
clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

env-info: ## Show environment information
	@echo "Environment Information:"
	@echo "======================="
	@echo "Python version: $$(python --version)"
	@echo "UV version: $$(/home/runner/.local/bin/uv --version)"
	@echo "Package location: $$(python -c 'import biosample_enricher; print(biosample_enricher.__file__)')" 2>/dev/null || echo "Package not installed"
	@echo ""

# Example and demo targets
run-example: ## Run example usage
	@echo "Creating example input file..."
	@echo '[{"sample_id": "EXAMPLE001", "organism": "Homo sapiens", "location": "Boston, MA"}, {"sample_id": "EXAMPLE002", "organism": "Escherichia coli", "tissue_type": "culture"}]' > /tmp/example_samples.json
	@echo ""
	@echo "Running enrichment on example samples:"
	@echo "======================================"
	~/.local/bin/uv run biosample-enricher enrich --input-file /tmp/example_samples.json --pretty
	@echo ""
	@echo "Running single sample enrichment:"
	@echo "=================================="
	~/.local/bin/uv run biosample-enricher enrich-single --sample-id "CLI001" --organism "Mus musculus" --location "Cambridge, MA" --pretty
	@rm -f /tmp/example_samples.json

demo: run-example ## Run demonstration of the tool

# Development workflow targets
dev-setup: setup-dev ## Complete development setup
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."

pre-commit: check test ## Run pre-commit checks (linting, formatting, type-check, tests)

ci: install-dev check test ## Run CI pipeline (install, check, test)

# Release workflow
pre-release: clean check test build ## Prepare for release (clean, check, test, build)
	@echo "Release preparation complete!"
	@echo "Built packages are in dist/"

# Quick development commands
dev: install-dev ## Quick development install

quick-test: ## Quick test run (no coverage)
	~/.local/bin/uv run pytest -x --tb=short

watch-test: ## Watch for changes and run tests
	~/.local/bin/uv run pytest-watch

# Documentation targets (placeholder for future use)
docs: ## Generate documentation (placeholder)
	@echo "Documentation generation not yet implemented"

docs-serve: ## Serve documentation locally (placeholder)
	@echo "Documentation serving not yet implemented"

# Security and dependency management
security-check: ## Run security checks (placeholder)
	@echo "Security checking not yet implemented"
	@echo "Consider adding: bandit, safety, or similar tools"

update-deps: ## Update dependencies
	~/.local/bin/uv pip compile --upgrade requirements-dev.txt || echo "No requirements file to update"

# Show package info
info: env-info ## Show package and environment information
	@echo "Package Information:"
	@echo "==================="
	@~/.local/bin/uv run biosample-enricher info 2>/dev/null || echo "Package not installed or not in PATH"