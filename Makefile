# Declare all targets that don't create files as .PHONY
.PHONY: install install-dev \
	test test-cov test-watch test-unit test-integration test-network test-slow test-fast test-cache test-cache-network test-sunrise-demo \
	lint lint-fix format format-check type-check dep-check check check-ci auto-fix-ci \
	build clean clean-all \
	pre-commit-install pre-commit-run \
	dev-setup dev-check \
	version \
	analyze-schemas clean-schema \
	demo-core demo-infrastructure demo-advanced demo-all demo-mongodb-dependent demo-mock-data \
	clean-adapters clean-all-outputs \
	validate-synthetic validate-biosamples validate-biosamples-make \
	cache-stats cache-query cache-clear cache-test cache-export \
	elevation-test elevation-batch elevation-all clean-elevation \
	metrics-local clean-metrics
.DEFAULT_GOAL := test

## Installation
install: ## Install the package in production mode
	@echo "Installing package..."
	uv sync

install-dev: ## Install package with development dependencies
	@echo "Installing package with dev dependencies..."
	uv sync --dev

## Testing
test: ## Run tests with timing
	@echo "Running tests with timing..."
	uv run pytest tests/ -v --durations=0

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	uv run pytest tests/ -v --cov=biosample_enricher --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	@echo "Running tests in watch mode..."
	uv run pytest tests/ -v --cov=biosample_enricher -f

test-unit: ## Run unit tests only (fast, no external dependencies)
	@echo "Running unit tests..."
	uv run pytest tests/ -v -m "unit"

test-integration: ## Run integration tests (includes database/mock dependencies)
	@echo "Running integration tests..."
	uv run pytest tests/ -v -m "integration"

test-network: ## Run network tests (requires internet connection)
	@echo "Running network tests..."
	uv run pytest tests/ -v -m "network"

test-slow: ## Run slow tests (includes timing-dependent tests)
	@echo "Running slow tests..."
	uv run pytest tests/ -v -m "slow"

test-fast: ## Run fast tests (excludes slow and network tests)
	@echo "Running fast tests..."
	uv run pytest tests/ -v -m "not slow and not network"

test-cache: ## Run HTTP cache tests specifically
	@echo "Running HTTP cache tests..."
	uv run pytest tests/test_http_cache.py -v

test-cache-network: ## Run HTTP cache network integration tests
	@echo "Running HTTP cache network tests..."
	uv run pytest tests/test_http_cache.py -v -m "network"

test-sunrise-demo: ## Run Sunrise-Sunset API cache demonstration (requires internet)
	@echo "Running Sunrise-Sunset API cache demonstration..."
	@echo "Note: This requires internet connection to api.sunrise-sunset.org"
	uv run python tests/examples/test_sunrise_api_demo.py

## Code Quality
lint: ## Run linting with ruff
	@echo "Running linting..."
	uv run ruff check biosample_enricher/ tests/

lint-fix: ## Run linting with auto-fix
	@echo "Running linting with auto-fix..."
	uv run ruff check --fix biosample_enricher/ tests/

format: ## Format code with ruff
	@echo "Formatting code..."
	uv run ruff format biosample_enricher/ tests/

format-check: ## Check if code is formatted
	@echo "Checking code formatting..."
	uv run ruff format --check biosample_enricher/ tests/

type-check: ## Run type checking with mypy
	@echo "Running type checking..."
	uv run mypy biosample_enricher/

dep-check: ## Check for unused dependencies with deptry
	@echo "Checking dependencies..."
	uv run deptry .

## Combined checks
check: lint type-check dep-check test ## Run all checks (lint, type-check, dep-check, test)
	@echo "All checks completed!"

check-ci: format lint type-check dep-check test ## Run all CI checks (format, lint, type-check, dep-check, test)
	@echo "All CI checks completed!"

auto-fix-ci: ## Automatically fix CI issues in a loop until all checks pass
	@echo "Running auto-fix CI loop..."
	@.github/hooks/auto-fix-ci.sh

## Package building
build: ## Build the package
	@echo "Building package..."
	uv build

clean: ## Clean build artifacts and cache
	@echo "Cleaning build artifacts..."
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

clean-all: clean clean-all-outputs ## Clean everything (artifacts, cache, and all generated outputs)
	@echo "Complete cleanup finished"

## Development tools
pre-commit-install: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	@echo "Running pre-commit on all files..."
	uv run pre-commit run --all-files

## Application commands

## Development workflow shortcuts
dev-setup: install-dev pre-commit-install ## Complete development setup
	@echo "Setting up git backup filter for precious files..."
	@git config filter.backup-precious.clean 'sh -c "mkdir -p .backups && tee .backups/$$(basename \"$$1\").$$(date +%s)" --'
	@git config filter.backup-precious.smudge cat
	@echo "Development environment setup complete!"
	@echo ""
	@echo "🛡️  Protection enabled for precious LLM-generated files:"
	@echo "   • Pre-commit hooks will warn before deletion"
	@echo "   • Git filter automatically backs up changes to .backups/"
	@echo "   • Use 'git commit --no-verify' to override protection"

dev-check: format lint type-check test ## Quick development check
	@echo "Development check complete!"

## Version management
version: ## Show current version
	@echo "Current version:"
	@uv run biosample-version


## Biosample Adapter Infrastructure
# MongoDB connection defaults (can be overridden) 
MONGO_URI ?= mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin
NMDC_DB ?= nmdc
GOLD_DB ?= gold_metadata


# Directory creation targets (not .PHONY since they create directories)
data/outputs/schema:
	@echo "Creating schema analysis directory..."
	@mkdir -p $@

# Schema inference from MongoDB collections
data/outputs/schema/nmdc_biosample_schema.json: | data/outputs/schema
	@echo "Inferring NMDC biosample schema from MongoDB..."
	uv run schema-inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-json-schema $@

data/outputs/schema/gold_biosample_schema.json: | data/outputs/schema
	@echo "Inferring GOLD biosample schema from MongoDB..."
	uv run schema-inference \
		--mongo-uri "$(MONGO_URI)" \
		--db $(GOLD_DB) \
		--coll biosamples \
		--sample-size 50000 \
		--out-json-schema $@

# Schema statistics generation
data/outputs/schema/nmdc_biosample_stats.csv: | data/outputs/schema
	@echo "Generating NMDC biosample field statistics..."
	uv run schema-statistics \
		--mongo-uri "$(MONGO_URI)" \
		--db $(NMDC_DB) \
		--coll biosample_set \
		--sample-size 50000 \
		--out-csv $@ \
		--out-md data/outputs/schema/nmdc_biosample_stats.md

data/outputs/schema/gold_biosample_stats.csv: | data/outputs/schema
	@echo "Generating GOLD biosample field statistics..."
	uv run schema-statistics \
		--mongo-uri "$(MONGO_URI)" \
		--db $(GOLD_DB) \
		--coll biosamples \
		--sample-size 50000 \
		--out-csv $@ \
		--out-md data/outputs/schema/gold_biosample_stats.md

# Claude CLI schema comparison
data/outputs/schema/schema_comparison_raw.json: data/outputs/schema/nmdc_biosample_schema.json data/outputs/schema/gold_biosample_schema.json prompts/schema-comparison-prompt.txt | data/outputs/schema
	@echo "Running Claude CLI schema comparison..."
	date && time claude --print --output-format json < prompts/schema-comparison-prompt.txt > $@

data/outputs/schema/schema_comparison.json: data/outputs/schema/schema_comparison_raw.json
	@echo "Extracting schema comparison JSON from Claude response..."
	jq -r '.result | fromjson' $< > $@

# Claude CLI enrichment analysis
data/outputs/schema/enrichment_analysis_raw.json: data/outputs/schema/nmdc_biosample_stats.csv data/outputs/schema/gold_biosample_stats.csv data/outputs/schema/schema_comparison.json prompts/enrichment-analysis-prompt.txt | data/outputs/schema
	@echo "Running Claude CLI enrichment analysis..."
	date && time claude --print --output-format json < prompts/enrichment-analysis-prompt.txt > $@

data/outputs/schema/enrichment_analysis.json: data/outputs/schema/enrichment_analysis_raw.json
	@echo "Extracting enrichment analysis JSON from Claude response..."
	jq -r '.result | fromjson' $< > $@

# Meta-targets for complete workflows
analyze-schemas: data/outputs/schema/nmdc_biosample_schema.json data/outputs/schema/gold_biosample_schema.json data/outputs/schema/nmdc_biosample_stats.csv data/outputs/schema/gold_biosample_stats.csv data/outputs/schema/schema_comparison.json data/outputs/schema/enrichment_analysis.json ## Complete schema analysis workflow
	@echo "Complete schema analysis workflow finished"

# Clean schema analysis outputs
clean-schema: ## Clean all schema analysis outputs
	@echo "Cleaning schema analysis outputs..."
	@rm -rf data/outputs/schema/
	@echo "Schema analysis outputs cleaned"

## Biosample Adapter Demonstrations
# Create output directories for adapter demonstrations
data/outputs/adapters:
	@echo "Creating adapter demonstration directory..."
	@mkdir -p $@

# Core Adapter Tests
data/outputs/adapters/nmdc_adapter_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run nmdc-adapter-demo --output-file $@

data/outputs/adapters/gold_adapter_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run gold-adapter-demo --output-file $@

data/outputs/adapters/unified_adapter_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run unified-adapter-demo --output-file $@

# Infrastructure Tests
data/outputs/adapters/mongodb_adapter_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	@echo "Note: Requires MongoDB connection at $(MONGO_URI)"
	@mkdir -p $(dir $@)
	uv run mongodb-connection-demo --output-file $@

data/outputs/adapters/pydantic_validation_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run pydantic-validation-demo --output-file $@

# Advanced Features
data/outputs/adapters/id_retrieval_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run id-retrieval-demo --output-file $@

data/outputs/adapters/random_sampling_test.json: | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	@echo "Note: Requires MongoDB connection at $(MONGO_URI)"
	@mkdir -p $(dir $@)
	uv run random-sampling-demo --output-file $@

# Synthetic biosample validation with output file target
data/outputs/adapters/synthetic_validation_test.json: data/input/synthetic_biosamples.json | data/outputs/adapters
	@echo "Generating $(notdir $@)..."
	uv run synthetic-validation-demo --input-file $< --output-file $@


# Standalone validation target
validate-synthetic: ## Validate synthetic biosamples and show results
	@echo "Validating synthetic biosamples..."
	@uv run synthetic-validation-demo --input-file data/input/synthetic_biosamples.json

# Flexible validation target with click options
validate-biosamples: ## Validate biosamples with click options (usage: make validate-biosamples OPTS="--input-file file.json --output-file results.json")
	@echo "Validating biosamples with options: $(OPTS)..."
	@uv run synthetic-validation-demo $(OPTS)

# Alternative validation target with make parameters (for backward compatibility)
validate-biosamples-make: ## Validate biosamples (usage: make validate-biosamples-make INPUT=file.json OUTPUT=results.json)
	@echo "Validating biosamples from $(INPUT)..."
	@if [ -n "$(OUTPUT)" ]; then \
		uv run synthetic-validation-demo --input-file $(INPUT) --output-file $(OUTPUT); \
	else \
		uv run synthetic-validation-demo --input-file $(INPUT); \
	fi


# Meta-targets for demonstration workflows
demo-core: data/outputs/adapters/nmdc_adapter_test.json data/outputs/adapters/gold_adapter_test.json data/outputs/adapters/unified_adapter_test.json ## Run core adapter demonstrations

demo-infrastructure: data/outputs/adapters/mongodb_adapter_test.json data/outputs/adapters/pydantic_validation_test.json ## Run infrastructure demonstrations

demo-advanced: data/outputs/adapters/id_retrieval_test.json data/outputs/adapters/random_sampling_test.json ## Run advanced feature demonstrations

demo-all: demo-core demo-infrastructure demo-advanced ## Run all adapter demonstrations
	@echo "All adapter demonstrations completed!"
	@ls -la data/outputs/adapters/*.json

demo-mongodb-dependent: data/outputs/adapters/mongodb_adapter_test.json data/outputs/adapters/random_sampling_test.json ## Run demonstrations that require MongoDB

demo-mock-data: data/outputs/adapters/nmdc_adapter_test.json data/outputs/adapters/gold_adapter_test.json data/outputs/adapters/unified_adapter_test.json data/outputs/adapters/pydantic_validation_test.json data/outputs/adapters/id_retrieval_test.json data/outputs/adapters/synthetic_validation_test.json ## Run demonstrations using mock data


# Clean adapter demonstration outputs
clean-adapters: ## Clean all adapter demonstration outputs
	@echo "Cleaning adapter demonstration outputs..."
	@rm -rf data/outputs/adapters/
	@echo "Adapter demonstration outputs cleaned"

# Clean all adapter/normalization work (schema + adapters)
clean-all-outputs: clean-schema clean-adapters ## Clean all schema analysis and adapter demonstration outputs
	@echo "Cleaning all adapter/normalization outputs..."
	@rm -rf data/outputs/
	@echo "All adapter/normalization outputs cleaned"


## HTTP Cache Management
cache-stats: ## Show HTTP cache statistics
	@echo "HTTP Cache Statistics:"
	@uv run http-cache-manager stats

cache-query: ## Query cache entries (usage: make cache-query CACHE_OPTS="--method GET --limit 10")
	@echo "Querying HTTP cache..."
	@uv run http-cache-manager query $(CACHE_OPTS)

cache-clear: ## Clear HTTP cache (usage: make cache-clear [HOURS=24] to clear entries older than N hours)
	@echo "Clearing HTTP cache..."
	@if [ -n "$(HOURS)" ]; then \
		uv run http-cache-manager clear --older-than-hours $(HOURS) --confirm; \
	else \
		uv run http-cache-manager clear --confirm; \
	fi

cache-test: ## Test cache functionality with a sample request
	@echo "Testing HTTP cache functionality..."
	@uv run http-cache-manager test --url "https://httpbin.org/json"

cache-export: ## Export cache entries to JSON (usage: make cache-export OUTPUT=cache_export.json)
	@echo "Exporting HTTP cache..."
	@if [ -n "$(OUTPUT)" ]; then \
		uv run http-cache-manager export --output $(OUTPUT); \
	else \
		uv run http-cache-manager export --output data/outputs/cache_export.json; \
	fi

## Elevation Service Demonstrations
data/outputs/elevation:
	@echo "Creating elevation output directory..."
	@mkdir -p $@

# Single coordinate elevation lookup
data/outputs/elevation/mount_rushmore.json: | data/outputs/elevation
	@echo "Testing elevation lookup for Mount Rushmore..."
	uv run elevation-lookup lookup --lat 43.8791 --lon -103.4591 \
		--subject-id "mount-rushmore-demo" \
		--output $@

data/outputs/elevation/london_uk.json: | data/outputs/elevation
	@echo "Testing elevation lookup for London, UK..."
	uv run elevation-lookup lookup --lat 51.5074 --lon -0.1278 \
		--subject-id "london-uk-demo" \
		--output $@

data/outputs/elevation/ocean_pacific.json: | data/outputs/elevation
	@echo "Testing elevation lookup for Pacific Ocean..."
	uv run elevation-lookup lookup --lat 20.0 --lon -150.0 \
		--subject-id "pacific-ocean-demo" \
		--output $@

# Elevation test with cache options
data/outputs/elevation/cache_test.json: | data/outputs/elevation
	@echo "Testing elevation lookup with cache disabled..."
	uv run elevation-lookup lookup --lat 37.7749 --lon -122.4194 \
		--subject-id "san-francisco-no-cache" \
		--no-cache \
		--output $@

# Provider comparison
data/outputs/elevation/provider_comparison.json: | data/outputs/elevation
	@echo "Comparing elevation providers for Mount Rushmore..."
	uv run elevation-demos compare-providers --lat 43.8791 --lon -103.4591 \
		--output $@

# Batch processing of synthetic biosamples
data/outputs/elevation/synthetic_biosamples.jsonl: data/input/synthetic_biosamples.json | data/outputs/elevation
	@echo "Processing elevation for synthetic biosamples..."
	uv run elevation-demos process-biosamples --input-file $< --output-file $@ \
		--batch-size 5 \
		--timeout 30 \
		--format jsonl

data/outputs/elevation/synthetic_biosamples.csv: data/input/synthetic_biosamples.json | data/outputs/elevation
	@echo "Processing elevation for synthetic biosamples (CSV output)..."
	uv run elevation-demos process-biosamples --input-file $< --output-file $@ \
		--batch-size 3 \
		--timeout 30 \
		--format csv

data/outputs/elevation/synthetic_biosamples_no_cache.jsonl: data/input/synthetic_biosamples.json | data/outputs/elevation
	@echo "Processing elevation for synthetic biosamples without cache..."
	uv run elevation-demos process-biosamples --input-file $< --output-file $@ \
		--batch-size 2 \
		--timeout 30 \
		--format jsonl \
		--no-cache


# Elevation meta-targets
elevation-test: data/outputs/elevation/mount_rushmore.json data/outputs/elevation/london_uk.json data/outputs/elevation/cache_test.json ## Test elevation CLI with various coordinates

elevation-batch: data/outputs/elevation/synthetic_biosamples.jsonl data/outputs/elevation/synthetic_biosamples.csv ## Run batch elevation processing

elevation-all: elevation-test elevation-batch data/outputs/elevation/provider_comparison.json ## Run all elevation demonstrations

# Clean elevation outputs
clean-elevation: ## Remove all elevation output files
	@echo "Cleaning elevation outputs..."
	rm -rf data/outputs/elevation/

## Enrichment Metrics Evaluation
data/outputs/metrics:
	@echo "Creating metrics output directory..."
	@mkdir -p $@

# Parameterizable metrics evaluation
NMDC_SAMPLES ?= 5
GOLD_SAMPLES ?= 5

metrics-local: | data/outputs/metrics ## Run metrics evaluation (usage: make metrics-local [NMDC_SAMPLES=N] [GOLD_SAMPLES=N])
	@echo "Running metrics evaluation with $(NMDC_SAMPLES) NMDC and $(GOLD_SAMPLES) GOLD samples..."
	@echo "Using MongoDB: $(MONGO_URI)"
	@echo "NMDC database: $(NMDC_DB), GOLD database: $(GOLD_DB)"
	NMDC_MONGO_CONNECTION="mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin" \
	GOLD_MONGO_CONNECTION="mongodb://ncbi_reader:register_manatee_coach78@localhost:27778/?directConnection=true&authMechanism=DEFAULT&authSource=admin" \
	uv run biosample-enricher metrics evaluate \
		--nmdc-samples $(NMDC_SAMPLES) \
		--gold-samples $(GOLD_SAMPLES) \
		--output-dir data/outputs/metrics \
		--create-plots $(EXTRA_ARGS)

# Clean metrics outputs
clean-metrics: ## Remove all metrics output files
	@echo "Cleaning metrics outputs..."
	rm -rf data/outputs/metrics/