.PHONY: help install install-dev test test-cov lint format type-check check clean build docs run schema-dirs analyze-schemas clean-schema adapter-dirs demo-core demo-infrastructure demo-advanced demo-all demo-mongodb-dependent demo-mock-data clean-adapters clean-all-outputs show-demo-results validate-demo-outputs validate-synthetic validate-biosamples validate-biosamples-make elevation-dirs elevation-demo elevation-test elevation-batch elevation-compare-providers clean-elevation
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
test: ## Run tests with timing
	@echo "$(GREEN)Running tests with timing...$(RESET)"
	uv run pytest tests/ -v --durations=0

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	uv run pytest tests/ -v --cov=biosample_enricher --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(RESET)"
	uv run pytest tests/ -v --cov=biosample_enricher -f

test-unit: ## Run unit tests only (fast, no external dependencies)
	@echo "$(GREEN)Running unit tests...$(RESET)"
	uv run pytest tests/ -v -m "unit"

test-integration: ## Run integration tests (includes database/mock dependencies)
	@echo "$(GREEN)Running integration tests...$(RESET)"
	uv run pytest tests/ -v -m "integration"

test-network: ## Run network tests (requires internet connection)
	@echo "$(GREEN)Running network tests...$(RESET)"
	uv run pytest tests/ -v -m "network"

test-slow: ## Run slow tests (includes timing-dependent tests)
	@echo "$(GREEN)Running slow tests...$(RESET)"
	uv run pytest tests/ -v -m "slow"

test-fast: ## Run fast tests (excludes slow and network tests)
	@echo "$(GREEN)Running fast tests...$(RESET)"
	uv run pytest tests/ -v -m "not slow and not network"

test-cache: ## Run HTTP cache tests specifically
	@echo "$(GREEN)Running HTTP cache tests...$(RESET)"
	uv run pytest tests/test_http_cache.py -v

test-cache-network: ## Run HTTP cache network integration tests
	@echo "$(GREEN)Running HTTP cache network tests...$(RESET)"
	uv run pytest tests/test_http_cache.py -v -m "network"

test-sunrise-demo: ## Run Sunrise-Sunset API cache demonstration (requires internet)
	@echo "$(GREEN)Running Sunrise-Sunset API cache demonstration...$(RESET)"
	@echo "$(YELLOW)Note: This requires internet connection to api.sunrise-sunset.org$(RESET)"
	uv run python tests/examples/test_sunrise_api_demo.py

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

dep-check: ## Check for unused dependencies with deptry
	@echo "$(GREEN)Checking dependencies...$(RESET)"
	uv run deptry .

## Combined checks
check: lint type-check dep-check test ## Run all checks (lint, type-check, dep-check, test)
	@echo "$(GREEN)All checks completed!$(RESET)"

check-ci: lint format-check type-check dep-check test ## Run all CI checks (lint, format-check, type-check, dep-check, test)
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
	@uv run biosample-version

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

## Biosample Adapter Infrastructure
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
	uv run schema-inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-json-schema $@

data/outputs/schema/gold_biosample_schema.json: schema-dirs
	@echo "$(GREEN)Inferring GOLD biosample schema from MongoDB...$(RESET)"
	uv run schema-inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(GOLD_DB) \
		--coll biosamples \
		--sample-size 50000 \
		--out-json-schema $@

# Schema statistics generation
data/outputs/schema/nmdc_biosample_stats.csv: schema-dirs
	@echo "$(GREEN)Generating NMDC biosample field statistics...$(RESET)"
	uv run schema-statistics \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-csv $@ \
		--out-md data/outputs/schema/nmdc_biosample_stats.md

data/outputs/schema/gold_biosample_stats.csv: schema-dirs
	@echo "$(GREEN)Generating GOLD biosample field statistics...$(RESET)"
	uv run schema-statistics \
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

## Biosample Adapter Demonstrations
# Create output directories for adapter demonstrations
adapter-dirs: ## Create adapter demonstration output directories
	@echo "$(GREEN)Creating adapter demonstration directories...$(RESET)"
	@mkdir -p data/outputs/adapters

# Core Adapter Tests
data/outputs/adapters/nmdc_adapter_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run nmdc-adapter-demo --output-file $@

data/outputs/adapters/gold_adapter_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run gold-adapter-demo --output-file $@

data/outputs/adapters/unified_adapter_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run unified-adapter-demo --output-file $@

# Infrastructure Tests
data/outputs/adapters/mongodb_adapter_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@echo "$(YELLOW)Note: Requires MongoDB connection at $(MONGO_URI)$(RESET)"
	@mkdir -p $(dir $@)
	uv run mongodb-connection-demo --output-file $@

data/outputs/adapters/pydantic_validation_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run pydantic-validation-demo --output-file $@

# Advanced Features
data/outputs/adapters/id_retrieval_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run id-retrieval-demo --output-file $@

data/outputs/adapters/random_sampling_test.json: adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@echo "$(YELLOW)Note: Requires MongoDB connection at $(MONGO_URI)$(RESET)"
	@mkdir -p $(dir $@)
	uv run random-sampling-demo --output-file $@

# Synthetic biosample validation with output file target
data/outputs/adapters/synthetic_validation_test.json: data/input/synthetic_biosamples.json adapter-dirs
	@echo "$(GREEN)Generating $(notdir $@)...$(RESET)"
	@mkdir -p $(dir $@)
	uv run synthetic-validation-demo --input-file $< --output-file $@

# File target for validation results (follows make convention: target name = output file)
validate-synthetic-biosamples: data/outputs/adapters/synthetic_validation_test.json ## Generate validation results file for synthetic biosamples
	@echo "$(GREEN)✅ Synthetic biosample validation completed: $<$(RESET)"

# Standalone validation target
validate-synthetic: ## Validate synthetic biosamples and show results
	@echo "$(GREEN)Validating synthetic biosamples...$(RESET)"
	@uv run synthetic-validation-demo --input-file data/input/synthetic_biosamples.json

# Flexible validation target with click options
validate-biosamples: ## Validate biosamples with click options (usage: make validate-biosamples OPTS="--input-file file.json --output-file results.json")
	@echo "$(GREEN)Validating biosamples with options: $(OPTS)...$(RESET)"
	@uv run synthetic-validation-demo $(OPTS)

# Alternative validation target with make parameters (for backward compatibility)
validate-biosamples-make: ## Validate biosamples (usage: make validate-biosamples-make INPUT=file.json OUTPUT=results.json)
	@echo "$(GREEN)Validating biosamples from $(INPUT)...$(RESET)"
	@if [ -n "$(OUTPUT)" ]; then \
		uv run synthetic-validation-demo --input-file $(INPUT) --output-file $(OUTPUT); \
	else \
		uv run synthetic-validation-demo --input-file $(INPUT); \
	fi

# Meta-targets for demonstration workflows (phony targets that aggregate file targets)
demo-core: data/outputs/adapters/nmdc_adapter_test.json data/outputs/adapters/gold_adapter_test.json data/outputs/adapters/unified_adapter_test.json ## Run core adapter demonstrations
	@echo "$(GREEN)✅ Core adapter demonstrations completed$(RESET)"

demo-infrastructure: data/outputs/adapters/mongodb_adapter_test.json data/outputs/adapters/pydantic_validation_test.json ## Run infrastructure demonstrations
	@echo "$(GREEN)✅ Infrastructure demonstrations completed$(RESET)"

demo-advanced: data/outputs/adapters/id_retrieval_test.json data/outputs/adapters/random_sampling_test.json ## Run advanced feature demonstrations
	@echo "$(GREEN)✅ Advanced feature demonstrations completed$(RESET)"

demo-all: demo-core demo-infrastructure demo-advanced ## Run all adapter demonstrations
	@echo "$(GREEN)🎉 All adapter demonstrations completed!$(RESET)"
	@echo "$(CYAN)Output files generated:$(RESET)"
	@ls -la data/outputs/adapters/*.json

# MongoDB-dependent demonstrations (require real database connection)
demo-mongodb-dependent: data/outputs/adapters/mongodb_adapter_test.json data/outputs/adapters/random_sampling_test.json ## Run demonstrations that require MongoDB
	@echo "$(GREEN)✅ MongoDB-dependent demonstrations completed$(RESET)"

# Mock data demonstrations (work without MongoDB)
demo-mock-data: data/outputs/adapters/nmdc_adapter_test.json data/outputs/adapters/gold_adapter_test.json data/outputs/adapters/unified_adapter_test.json data/outputs/adapters/pydantic_validation_test.json data/outputs/adapters/id_retrieval_test.json data/outputs/adapters/synthetic_validation_test.json ## Run demonstrations using mock data
	@echo "$(GREEN)✅ Mock data demonstrations completed$(RESET)"

# Clean adapter demonstration outputs
clean-adapters: ## Clean all adapter demonstration outputs
	@echo "$(GREEN)🧹 Cleaning adapter demonstration outputs...$(RESET)"
	@rm -rf data/outputs/adapters/
	@echo "$(GREEN)✅ Adapter demonstration outputs cleaned$(RESET)"

# Clean all adapter/normalization work (schema + adapters)
clean-all-outputs: clean-schema clean-adapters ## Clean all schema analysis and adapter demonstration outputs
	@echo "$(GREEN)🧹 Cleaning all adapter/normalization outputs...$(RESET)"
	@rm -rf data/outputs/
	@echo "$(GREEN)✅ All adapter/normalization outputs cleaned$(RESET)"

# Show demonstration results
show-demo-results: ## Show summary of demonstration results
	@echo "$(CYAN)Adapter Demonstration Results Summary:$(RESET)"
	@echo ""
	@if [ -d "data/outputs/adapters" ]; then \
		for file in data/outputs/adapters/*.json; do \
			if [ -f "$$file" ]; then \
				echo "$(GREEN)📄 $$(basename $$file)$(RESET)"; \
				echo "   Size: $$(wc -c < "$$file") bytes"; \
				echo "   Generated: $$(stat -f "%Sm" "$$file")"; \
				echo ""; \
			fi; \
		done; \
	else \
		echo "$(YELLOW)No demonstration results found. Run 'make demo-all' first.$(RESET)"; \
	fi

# Validate demonstration outputs
validate-demo-outputs: ## Validate that all demonstration outputs are valid JSON
	@echo "$(GREEN)Validating demonstration outputs...$(RESET)"
	@if [ -d "data/outputs/adapters" ]; then \
		for file in data/outputs/adapters/*.json; do \
			if [ -f "$$file" ]; then \
				echo "Validating $$(basename $$file)..."; \
				if jq empty "$$file" 2>/dev/null; then \
					echo "$(GREEN)✅ $$(basename $$file) is valid JSON$(RESET)"; \
				else \
					echo "$(RED)❌ $$(basename $$file) is invalid JSON$(RESET)"; \
				fi; \
			fi; \
		done; \
	else \
		echo "$(YELLOW)No demonstration outputs found.$(RESET)"; \
	fi

## HTTP Cache Management
cache-stats: ## Show HTTP cache statistics
	@echo "$(GREEN)HTTP Cache Statistics:$(RESET)"
	@uv run http-cache-manager stats

cache-query: ## Query cache entries (usage: make cache-query CACHE_OPTS="--method GET --limit 10")
	@echo "$(GREEN)Querying HTTP cache...$(RESET)"
	@uv run http-cache-manager query $(CACHE_OPTS)

cache-clear: ## Clear HTTP cache (usage: make cache-clear [HOURS=24] to clear entries older than N hours)
	@echo "$(GREEN)Clearing HTTP cache...$(RESET)"
	@if [ -n "$(HOURS)" ]; then \
		uv run http-cache-manager clear --older-than-hours $(HOURS) --confirm; \
	else \
		uv run http-cache-manager clear --confirm; \
	fi

cache-test: ## Test cache functionality with a sample request
	@echo "$(GREEN)Testing HTTP cache functionality...$(RESET)"
	@uv run http-cache-manager test "https://httpbin.org/json"

cache-export: ## Export cache entries to JSON (usage: make cache-export OUTPUT=cache_export.json)
	@echo "$(GREEN)Exporting HTTP cache...$(RESET)"
	@if [ -n "$(OUTPUT)" ]; then \
		uv run http-cache-manager export --output $(OUTPUT); \
	else \
		uv run http-cache-manager export --output data/outputs/cache_export.json; \
	fi

cache-help: ## Show cache management help
	@echo "$(CYAN)HTTP Cache Management Commands:$(RESET)"
	@echo ""
	@echo "$(GREEN)Basic Operations:$(RESET)"
	@echo "  make cache-stats          - Show cache statistics"
	@echo "  make cache-query          - Query cache entries"
	@echo "  make cache-clear          - Clear all cache entries"
	@echo "  make cache-test           - Test cache functionality"
	@echo ""
	@echo "$(GREEN)Advanced Operations:$(RESET)"
	@echo "  make cache-query CACHE_OPTS=\"--method GET --limit 10\""
	@echo "  make cache-clear HOURS=24  - Clear entries older than 24 hours"
	@echo "  make cache-export OUTPUT=my_cache.json"
	@echo ""
	@echo "$(GREEN)Direct CLI Usage:$(RESET)"
	@echo "  uv run http-cache-manager --help"
	@echo "  uv run http-cache-manager query --help"

## Elevation Service Demonstrations
elevation-dirs: ## Create elevation output directories
	@echo "$(GREEN)Creating elevation output directories...$(RESET)"
	@mkdir -p data/outputs/elevation

# Single coordinate elevation lookup
data/outputs/elevation/mount_rushmore.json: elevation-dirs
	@echo "$(GREEN)Testing elevation lookup for Mount Rushmore...$(RESET)"
	uv run elevation-lookup lookup --lat 43.8791 --lon -103.4591 \
		--subject-id "mount-rushmore-demo" \
		--output $@

data/outputs/elevation/london_uk.json: elevation-dirs
	@echo "$(GREEN)Testing elevation lookup for London, UK...$(RESET)"
	uv run elevation-lookup lookup --lat 51.5074 --lon -0.1278 \
		--subject-id "london-uk-demo" \
		--output $@

data/outputs/elevation/ocean_pacific.json: elevation-dirs
	@echo "$(GREEN)Testing elevation lookup for Pacific Ocean...$(RESET)"
	uv run elevation-lookup lookup --lat 20.0 --lon -150.0 \
		--subject-id "pacific-ocean-demo" \
		--output $@

# Elevation test with cache options
data/outputs/elevation/cache_test.json: elevation-dirs
	@echo "$(GREEN)Testing elevation lookup with cache disabled...$(RESET)"
	uv run elevation-lookup lookup --lat 37.7749 --lon -122.4194 \
		--subject-id "san-francisco-no-cache" \
		--no-cache \
		--output $@

# Provider comparison
data/outputs/elevation/provider_comparison.json: elevation-dirs
	@echo "$(GREEN)Comparing elevation providers for Mount Rushmore...$(RESET)"
	uv run elevation-demos compare-providers --lat 43.8791 --lon -103.4591 \
		--output $@

# Batch processing of synthetic biosamples
data/outputs/elevation/synthetic_biosamples.jsonl: data/input/synthetic_biosamples.json elevation-dirs
	@echo "$(GREEN)Processing elevation for synthetic biosamples...$(RESET)"
	uv run elevation-demos process-biosamples $< $@ \
		--batch-size 5 \
		--timeout 30 \
		--format jsonl

data/outputs/elevation/synthetic_biosamples.csv: data/input/synthetic_biosamples.json elevation-dirs
	@echo "$(GREEN)Processing elevation for synthetic biosamples (CSV output)...$(RESET)"
	uv run elevation-demos process-biosamples $< $@ \
		--batch-size 3 \
		--timeout 30 \
		--format csv

data/outputs/elevation/synthetic_biosamples_no_cache.jsonl: data/input/synthetic_biosamples.json elevation-dirs
	@echo "$(GREEN)Processing elevation for synthetic biosamples without cache...$(RESET)"
	uv run elevation-demos process-biosamples $< $@ \
		--batch-size 2 \
		--timeout 30 \
		--format jsonl \
		--no-cache

# Test elevation CLI functionality
elevation-test: data/outputs/elevation/mount_rushmore.json data/outputs/elevation/london_uk.json data/outputs/elevation/cache_test.json ## Test elevation CLI with various coordinates and options

elevation-demo: data/outputs/elevation/provider_comparison.json ## Run elevation provider comparison demo

elevation-batch: data/outputs/elevation/synthetic_biosamples.jsonl data/outputs/elevation/synthetic_biosamples.csv ## Run batch elevation processing demos

elevation-compare-providers: data/outputs/elevation/provider_comparison.json ## Compare elevation providers for a test coordinate

# Run all elevation demonstrations
elevation-all: elevation-test elevation-demo elevation-batch ## Run all elevation demonstrations

# Clean elevation outputs
clean-elevation: ## Remove all elevation output files
	@echo "$(RED)Cleaning elevation outputs...$(RESET)"
	rm -rf data/outputs/elevation/