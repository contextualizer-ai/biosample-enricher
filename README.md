# Biosample Enricher

Infer AI-friendly metadata about biosamples from multiple sources.

## Features

- **Click-based CLI** with comprehensive options (no positional arguments)
- **Type-safe** data models using Pydantic
- **Comprehensive testing** with pytest, coverage reporting
- **Code quality tools** including ruff (linting/formatting) and mypy (type checking)
- **Makefile automation** for all development tasks
- **UV package management** for fast, reliable dependency management
- **Caching support** for improved performance
- **Multiple output formats** (JSON, JSONL)

## Installation

### Using UV (Recommended)

```bash
# Install UV if not already installed
pip install uv

# Install the package
uv pip install -e .

# Or install with development dependencies
uv pip install -e ".[dev]"
```

### Development Setup

```bash
# Complete development setup
make dev-setup

# Or manually:
make install-dev
make setup-dev  # Sets up pre-commit hooks
```

## Usage

### Command Line Interface

The CLI uses options instead of positional arguments for all commands:

#### Enrich from File

```bash
# Enrich samples from JSON file
biosample-enricher enrich --input-file samples.json --output-file enriched.json --pretty

# Enrich with different output format
biosample-enricher enrich --input-file samples.json --format jsonl
```

#### Enrich Single Sample

```bash
# Enrich a single sample with comprehensive options
biosample-enricher enrich-single \
    --sample-id "SAMPLE001" \
    --sample-name "Test Sample" \
    --organism "Homo sapiens" \
    --tissue-type "blood" \
    --collection-date "2023-01-15" \
    --location "Boston, MA" \
    --metadata '{"study": "test_study"}' \
    --pretty

# Minimal example
biosample-enricher enrich-single --sample-id "MIN001"
```

#### Global Options

```bash
# Enable verbose output and custom timeout
biosample-enricher --verbose --api-timeout 60 --no-cache enrich-single --sample-id "TEST001"

# Get configuration info
biosample-enricher info
```

### Python API

```python
from biosample_enricher import BiosampleEnricher, BiosampleMetadata

# Create enricher
enricher = BiosampleEnricher(api_timeout=30.0, enable_caching=True)

# Create sample metadata
sample = BiosampleMetadata(
    sample_id="SAMPLE001",
    organism="Homo sapiens",
    location="Boston, MA"
)

# Enrich the sample
result = enricher.enrich_sample(sample)

print(f"Confidence: {result.confidence_score}")
print(f"Sources: {result.sources}")
print(f"Enriched data: {result.enriched_metadata.enriched_data}")
```

## Development

### Available Make Commands

```bash
make help                # Show all available commands
make dev-setup          # Complete development setup
make test               # Run tests
make test-cov           # Run tests with coverage
make lint               # Run linting
make format             # Format code
make type-check         # Run type checking
make check              # Run all quality checks
make build              # Build distribution packages
make clean              # Clean build artifacts
make run-example        # Run example usage
```

### Code Quality

This project uses:

- **ruff** for linting and code formatting
- **mypy** for static type checking
- **pytest** for testing with coverage reporting
- **pre-commit** hooks for automated quality checks

```bash
# Run all quality checks
make check

# Fix linting issues and format code
make check-fix

# Run tests with coverage
make test-cov
```

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run only fast tests
make test-fast

# Run specific test file
uv run pytest tests/test_cli.py -v
```

## Input Format

### JSON File Format

Single sample:
```json
{
    "sample_id": "SAMPLE001",
    "sample_name": "Test Sample",
    "organism": "Homo sapiens",
    "tissue_type": "blood",
    "collection_date": "2023-01-15",
    "location": "Boston, MA",
    "metadata": {
        "study": "test_study",
        "batch": "A"
    }
}
```

Multiple samples:
```json
[
    {
        "sample_id": "SAMPLE001",
        "organism": "Homo sapiens"
    },
    {
        "sample_id": "SAMPLE002",
        "organism": "Escherichia coli"
    }
]
```

## Output Format

```json
{
    "original": {
        "sample_id": "SAMPLE001",
        "organism": "Homo sapiens",
        "location": "Boston, MA",
        ...
    },
    "enriched": {
        "sample_id": "SAMPLE001",
        "organism": "Homo sapiens",
        "location": "Boston, MA",
        "enriched_data": {
            "organism_taxonomy": "taxonomy_for_homo_sapiens",
            "organism_kingdom": "Animalia",
            "organism_phylum": "Chordata",
            "location_normalized": "Boston, Ma"
        },
        ...
    },
    "confidence_score": 0.85,
    "sources": ["organism_database", "location_database"],
    "processing_time": 1.23
}
```

## License

This project is licensed under the terms specified in the LICENSE file.
