# Testing Standards for Biosample Enricher

This document outlines the testing standards and practices for the Biosample Enricher project, following LinkML community guidelines and modern Python testing best practices.

## Framework & How to Run

### Primary Testing Framework
- **pytest** is the standard framework for all new tests
- Legacy `unittest` code may exist but should be migrated to pytest when possible
- All test files should be named `test_*.py` and located under the `tests/` directory

### Common Test Invocations
```bash
# Run all tests
uv run pytest
make test

# Run tests with coverage
uv run pytest --cov=biosample_enricher --cov-report=term-missing
make test-cov

# Run specific test categories
uv run pytest -m "not network"        # Skip network tests
uv run pytest -m "not slow"           # Skip slow tests
uv run pytest -m "network"            # Run only network tests

# Update snapshots (if using snapshot testing)
uv run pytest --generate-snapshots

# Run tests in watch mode
uv run pytest -f
make test-watch
```

## Test Layout & Philosophy

### Directory Structure
```
tests/
├── test_core.py              # Core functionality tests
├── test_cli.py               # Command-line interface tests
├── test_http_cache.py         # HTTP caching system tests
├── test_models.py             # Data model tests
├── test_adapters.py           # Database adapter tests
├── fixtures/                  # Test data and fixtures
│   ├── sample_biosamples.json
│   └── mock_responses/
└── __snapshots__/             # Snapshot test outputs
    └── test_*.py/
```

### Testing Philosophy
1. **Small, focused tests**: Each test should verify one specific behavior
2. **Purpose-built fixtures**: Use small, controlled test data rather than large real datasets
3. **Test independence**: Tests should not depend on each other or external state
4. **Clear test names**: Test names should describe what is being tested
5. **Both positive and negative cases**: Test success paths and error conditions

## Pytest Marks & Fixtures

### Standard Test Marks

#### `@pytest.mark.network`
- Applied to tests that make real network requests
- **Skipped in CI** to avoid flaky tests and external dependencies
- Can be run locally for integration testing
- Example: Tests hitting the ISS Pass API

```python
@pytest.mark.network
def test_iss_api_integration(cached_client):
    """Test real API integration with ISS service."""
    response = cached_client.get("http://api.open-notify.org/iss-pass.json", 
                                params={"lat": 37.7749, "lon": -122.4194})
    assert response.status_code == 200
```

#### `@pytest.mark.slow`
- Applied to tests that take significant time (>1 second)
- **Skipped locally by default** for faster development cycles
- **Exercised in CI** for comprehensive testing
- Example: Cache expiration timing tests, performance tests

```python
@pytest.mark.slow
def test_cache_expiration_timing(cached_client):
    """Test cache expiration with real timing delays."""
    # Test implementation with time.sleep() calls
```

#### `@pytest.mark.unit`
- Fast, isolated unit tests
- No external dependencies (database, network, file system)
- Should comprise the majority of the test suite

#### `@pytest.mark.integration`
- Tests that exercise multiple components together
- May use test databases or mock external services
- Slower than unit tests but faster than network tests

### Common Fixtures

#### Test Data Fixtures
```python
@pytest.fixture
def sample_biosample():
    """Provide a standard test biosample."""
    return {
        "sample_id": "TEST001",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "collection_date": "2023-01-15"
    }

@pytest.fixture
def input_path():
    """Point to local, versioned test inputs."""
    return Path(__file__).parent / "fixtures"
```

#### Resource Management Fixtures
```python
@pytest.fixture
def clean_test_db():
    """Provide clean test database for each test."""
    # Setup: create clean database
    yield db_connection
    # Teardown: clean up database

@pytest.fixture
def temp_cache():
    """Provide temporary cache instance."""
    cache = create_test_cache()
    yield cache
    cache.close()
```

#### Snapshot Testing Fixtures
```python
@pytest.fixture
def snapshot():
    """Write expected artifacts to __snapshots__/."""
    # Implementation depends on snapshot testing library
    # Update with --generate-snapshots when outputs change
```

## Test Categories & Examples

### Unit Tests
Test individual components in isolation:

```python
class TestRequestCanonicalizer:
    def test_coordinate_rounding(self):
        canonicalizer = RequestCanonicalizer(coord_precision=4)
        params = {"lat": 37.774929, "lon": -122.419416}
        result = canonicalizer.canonicalize_params(params)
        assert result["lat"] == 37.7749
        assert result["lon"] == -122.4194
```

### Integration Tests
Test component interactions:

```python
class TestCacheIntegration:
    def test_cache_miss_and_hit_cycle(self, cached_client):
        # Test complete cache workflow
        response1 = cached_client.get(url)  # Should miss cache
        response2 = cached_client.get(url)  # Should hit cache
        assert getattr(response2, '_from_cache', False)
```

### Network Tests
Test real external service integration:

```python
@pytest.mark.network
class TestNetworkIntegration:
    def test_iss_api_cache_integration(self, cached_client):
        """Test complete integration with ISS Pass API."""
        url = "http://api.open-notify.org/iss-pass.json"
        params = {"lat": 37.7749, "lon": -122.4194}
        
        response = cached_client.get(url, params=params, timeout=10)
        assert response.status_code == 200
        assert response.json()["message"] == "success"
```

### Performance Tests
Test timing and performance characteristics:

```python
@pytest.mark.slow
class TestPerformance:
    def test_cache_performance(self, cached_client):
        # Measure cache hit vs miss performance
        start_time = time.time()
        # ... test implementation
        elapsed = time.time() - start_time
        assert elapsed < expected_threshold
```

## Example-Driven Validation

### Valid Examples
Place valid test data under `tests/fixtures/valid/`:
```
tests/fixtures/valid/
├── biosample_001.json
├── biosample_002.json
└── enrichment_response.json
```

### Invalid Examples  
Place invalid test data under `tests/fixtures/invalid/`:
```
tests/fixtures/invalid/
├── missing_required_field.json
├── invalid_coordinates.json
└── malformed_date.json
```

### Validation Pattern
```python
def test_valid_examples():
    """Test that valid examples pass validation."""
    valid_dir = Path("tests/fixtures/valid")
    for example_file in valid_dir.glob("*.json"):
        with open(example_file) as f:
            data = json.load(f)
        # Should not raise validation error
        BiosampleLocation(**data)

def test_invalid_examples():
    """Test that invalid examples fail validation."""
    invalid_dir = Path("tests/fixtures/invalid")
    for example_file in invalid_dir.glob("*.json"):
        with open(example_file) as f:
            data = json.load(f)
        # Should raise validation error
        with pytest.raises(ValidationError):
            BiosampleLocation(**data)
```

## Tooling & Style

### Development Environment
- **Dependency management**: `uv` (increasingly standard across LinkML repos)
- **Linting**: `ruff check` for code quality
- **Formatting**: `ruff format` for consistent style
- **Type checking**: `mypy` for static type analysis

### Pre-commit Hooks
Encouraged for consistent local enforcement:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

### CI Integration
GitHub Actions workflow typically includes:

```yaml
- name: Run tests
  run: |
    uv run pytest
    
- name: Run linting
  run: |
    uv run ruff check .
    uv run ruff format --check .
    
- name: Type checking
  run: |
    uv run mypy biosample_enricher/
```

## Mock Strategies

### External Services
Mock external API calls in unit tests:

```python
@patch('requests.Session.request')
def test_api_call(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    mock_request.return_value = mock_response
    
    # Test code that makes API calls
    result = make_api_call()
    assert result["test"] == "data"
```

### Database Operations
Use test databases or mock database operations:

```python
@pytest.fixture
def mock_mongo_collection():
    with patch('pymongo.collection.Collection') as mock_collection:
        yield mock_collection
        
def test_database_operation(mock_mongo_collection):
    # Test database interactions without real database
```

## Test Data Management

### Small Test Fixtures
Create minimal, focused test data:

```python
# Good: Minimal test data
@pytest.fixture
def minimal_biosample():
    return {
        "sample_id": "TEST001",
        "latitude": 37.7749,
        "longitude": -122.4194
    }

# Avoid: Large, complex test data that obscures test intent
```

### Parameterized Tests
Use parameterization for testing multiple scenarios:

```python
@pytest.mark.parametrize("input_coord,expected", [
    (37.774929, 37.7749),
    (-122.419416, -122.4194),
    (0.0, 0.0),
])
def test_coordinate_rounding(input_coord, expected):
    result = round_coordinate(input_coord, precision=4)
    assert result == expected
```

## Migration from unittest

When migrating existing `unittest` code to pytest:

1. **Remove unittest imports**: No need for `unittest.TestCase`
2. **Convert to functions**: Test methods become test functions
3. **Use pytest fixtures**: Replace `setUp`/`tearDown` with fixtures
4. **Use pytest assertions**: Replace `self.assertEqual` with `assert`
5. **Add pytest marks**: Apply appropriate marks for test categorization

```python
# Old unittest style
class TestExample(unittest.TestCase):
    def setUp(self):
        self.data = create_test_data()
    
    def test_something(self):
        self.assertEqual(process(self.data), expected_result)

# New pytest style
@pytest.fixture
def test_data():
    return create_test_data()

def test_something(test_data):
    assert process(test_data) == expected_result
```

## Running Tests

### Local Development
```bash
# Quick tests (skip slow and network tests)
uv run pytest -m "not slow and not network"

# All tests including slow ones
uv run pytest

# Network tests only (for integration testing)
uv run pytest -m network

# Specific test file
uv run pytest tests/test_http_cache.py

# Specific test function
uv run pytest tests/test_http_cache.py::test_coordinate_canonicalization
```

### Continuous Integration
CI should run comprehensive test suite:

```bash
# Standard CI test run
uv run pytest -m "not network" --cov=biosample_enricher

# Include slow tests in CI
uv run pytest -m "not network"
```

### Test Configuration
Configure pytest in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",                              # Show extra test summary
    "--strict-markers",                 # Require marker registration
    "--strict-config",                  # Strict configuration
    "--cov=biosample_enricher",        # Coverage for main package
    "--cov-report=term-missing",       # Show missing coverage
    "--cov-report=html",               # Generate HTML coverage report
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselected with -m 'not slow')",
    "network: marks tests as requiring network (deselected in CI)",
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests",
]
```

This testing framework provides a solid foundation for maintaining high code quality while supporting rapid development and reliable CI/CD processes.