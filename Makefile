.PHONY: help install install-dev test test-cov lint format type-check check clean build docs run schema-dirs analyze-schemas clean-schema
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[96m
GREEN := \033[92m
YELLOW := \033[93m
RED := \033[91m
RESET := \033[0m

## Help command
help: ## Show this help message
	@echo "$(CYAN)Biosample Enricher - Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Available commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## Installation
install: ## Install the package in production mode
	@echo "$(GREEN)Installing package...$(RESET)"
	uv sync

install-dev: ## Install package with development dependencies
	@echo "$(GREEN)Installing package with dev dependencies...$(RESET)"
	uv sync --dev

## Testing
test: ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	uv run pytest tests/ -v --cov=biosample_enricher --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(RESET)"
	uv run pytest tests/ -v --cov=biosample_enricher -f

## Code Quality
lint: ## Run linting with ruff
	@echo "$(GREEN)Running linting...$(RESET)"
	uv run ruff check biosample_enricher/ tests/

lint-fix: ## Run linting with auto-fix
	@echo "$(GREEN)Running linting with auto-fix...$(RESET)"
	uv run ruff check --fix biosample_enricher/ tests/

format: ## Format code with ruff
	@echo "$(GREEN)Formatting code...$(RESET)"
	uv run ruff format biosample_enricher/ tests/

format-check: ## Check if code is formatted
	@echo "$(GREEN)Checking code formatting...$(RESET)"
	uv run ruff format --check biosample_enricher/ tests/

type-check: ## Run type checking with mypy
	@echo "$(GREEN)Running type checking...$(RESET)"
	uv run mypy biosample_enricher/

## Combined checks
check: lint type-check test ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)All checks completed!$(RESET)"

check-ci: lint format-check type-check test ## Run all CI checks (lint, format-check, type-check, test)
	@echo "$(GREEN)All CI checks completed!$(RESET)"

## Package building
build: ## Build the package
	@echo "$(GREEN)Building package...$(RESET)"
	uv build

clean: ## Clean build artifacts and cache
	@echo "$(GREEN)Cleaning build artifacts...$(RESET)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

## Development tools
pre-commit-install: ## Install pre-commit hooks
	@echo "$(GREEN)Installing pre-commit hooks...$(RESET)"
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	@echo "$(GREEN)Running pre-commit on all files...$(RESET)"
	uv run pre-commit run --all-files

## Application commands
run: ## Run the CLI application (shows help)
	@echo "$(GREEN)Running biosample-enricher CLI...$(RESET)"
	uv run biosample-enricher --help

enrich-example: ## Run example enrichment command
	@echo "$(GREEN)Running example enrichment...$(RESET)"
	uv run biosample-enricher enrich --sample-id SAMN123456 --output-format table

validate-example: ## Run example validation command
	@echo "$(GREEN)Running example validation...$(RESET)"
	uv run biosample-enricher validate --sample-id SAMN123456

## Development workflow shortcuts
dev-setup: install-dev pre-commit-install ## Complete development setup
	@echo "$(GREEN)Development environment setup complete!$(RESET)"

dev-check: format lint type-check test ## Quick development check
	@echo "$(GREEN)Development check complete!$(RESET)"

## Docker (if needed in future)
docker-build: ## Build Docker image
	@echo "$(YELLOW)Docker build not implemented yet$(RESET)"

docker-run: ## Run Docker container
	@echo "$(YELLOW)Docker run not implemented yet$(RESET)"

## Version management
version: ## Show current version
	@echo "$(GREEN)Current version:$(RESET)"
	@uv run python -c "from biosample_enricher import __version__; print(__version__)"

## Documentation
docs: ## Generate documentation (placeholder)
	@echo "$(YELLOW)Documentation generation not implemented yet$(RESET)"

docs-serve: ## Serve documentation locally (placeholder)
	@echo "$(YELLOW)Documentation serving not implemented yet$(RESET)"

## Git shortcuts
git-status: ## Show git status
	@git status

git-log: ## Show recent git commits
	@git log --oneline -10

## Schema Analysis Infrastructure
# MongoDB connection defaults (can be overridden) 
MONGO_URI ?= mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin
NMDC_DB ?= nmdc
GOLD_DB ?= gold_metadata

schema-dirs: ## Create schema analysis directories
	@echo "$(GREEN)Creating schema analysis directories...$(RESET)"
	@mkdir -p data/outputs/schema

# Schema inference from MongoDB collections
data/outputs/schema/nmdc_biosample_schema.json: schema-dirs
	@echo "$(GREEN)Inferring NMDC biosample schema from MongoDB...$(RESET)"
	uv run python -m biosample_enricher.schema_inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-json-schema $@

data/outputs/schema/gold_biosample_schema.json: schema-dirs
	@echo "$(GREEN)Inferring GOLD biosample schema from MongoDB...$(RESET)"
	uv run python -m biosample_enricher.schema_inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(GOLD_DB) \
		--coll biosamples \
		--sample-size 50000 \
		--out-json-schema $@

# Schema statistics generation
data/outputs/schema/nmdc_biosample_stats.csv: schema-dirs
	@echo "$(GREEN)Generating NMDC biosample field statistics...$(RESET)"
	uv run python -m biosample_enricher.schema_statistics \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-csv $@ \
		--out-md data/outputs/schema/nmdc_biosample_stats.md

data/outputs/schema/gold_biosample_stats.csv: schema-dirs
	@echo "$(GREEN)Generating GOLD biosample field statistics...$(RESET)"
	uv run python -m biosample_enricher.schema_statistics \
		--mongo-uri "$(MONGO_URI)" \
		--db $(GOLD_DB) \
		--coll biosamples \
		--sample-size 50000 \
		--out-csv $@ \
		--out-md data/outputs/schema/gold_biosample_stats.md

# Claude CLI schema comparison
data/outputs/schema/schema_comparison_raw.json: data/outputs/schema/nmdc_biosample_schema.json data/outputs/schema/gold_biosample_schema.json prompts/schema-comparison-prompt.txt
	@echo "$(GREEN)Running Claude CLI schema comparison...$(RESET)"
	@mkdir -p $$(dirname $@)
	date && time claude --print --output-format json < prompts/schema-comparison-prompt.txt > $@

data/outputs/schema/schema_comparison.json: data/outputs/schema/schema_comparison_raw.json
	@echo "$(GREEN)Extracting schema comparison JSON from Claude response...$(RESET)"
	jq -r '.result | fromjson' $< > $@

# Claude CLI enrichment analysis
data/outputs/schema/enrichment_analysis_raw.json: data/outputs/schema/nmdc_biosample_stats.csv data/outputs/schema/gold_biosample_stats.csv data/outputs/schema/schema_comparison.json prompts/enrichment-analysis-prompt.txt
	@echo "$(GREEN)Running Claude CLI enrichment analysis...$(RESET)"
	@mkdir -p $$(dirname $@)
	date && time claude --print --output-format json < prompts/enrichment-analysis-prompt.txt > $@

data/outputs/schema/enrichment_analysis.json: data/outputs/schema/enrichment_analysis_raw.json
	@echo "$(GREEN)Extracting enrichment analysis JSON from Claude response...$(RESET)"
	jq -r '.result | fromjson' $< > $@

# Meta-targets for complete workflows
analyze-schemas: data/outputs/schema/nmdc_biosample_schema.json data/outputs/schema/gold_biosample_schema.json data/outputs/schema/nmdc_biosample_stats.csv data/outputs/schema/gold_biosample_stats.csv data/outputs/schema/schema_comparison.json data/outputs/schema/enrichment_analysis.json ## Complete schema analysis workflow
	@echo "$(GREEN)✅ Complete schema analysis workflow finished$(RESET)"

# Clean schema analysis outputs
clean-schema: ## Clean all schema analysis outputs
	@echo "$(GREEN)🧹 Cleaning schema analysis outputs...$(RESET)"
	@rm -rf data/outputs/schema/
	@echo "$(GREEN)✅ Schema analysis outputs cleaned$(RESET)"