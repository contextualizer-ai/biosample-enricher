# HTTP Cache Testing Implementation

This directory contains comprehensive tests for the MongoDB-based HTTP caching system, implemented following LinkML testing guidelines.

## Test Structure

### Test Files
- `test_http_cache.py` - Comprehensive HTTP cache testing with ISS API integration
- `test_cli.py` - Command-line interface tests (existing)
- `test_core.py` - Core functionality tests (existing)

### Test Categories

#### Unit Tests (`@pytest.mark.unit`)
Fast, isolated tests with no external dependencies:
- `TestRequestCanonicalizer` - Coordinate rounding, datetime truncation, URL canonicalization
- Basic cache key generation and validation logic
- Error handling and graceful degradation

#### Integration Tests (`@pytest.mark.integration`)
Tests exercising multiple components with mocked dependencies:
- `TestCachedHTTPClient` - Full cache workflow with mocked HTTP responses
- Cache miss/hit cycles, cache control parameters
- Different HTTP methods and canonicalization behavior

#### Network Tests (`@pytest.mark.network`)
Real external API integration (skipped in CI):
- `TestNetworkIntegration` - Live ISS Pass API testing
- Real coordinate canonicalization with API responses
- Performance comparison between cache hits and misses

#### Slow Tests (`@pytest.mark.slow`)
Performance and timing tests:
- Cache expiration timing with real delays
- High-volume caching performance
- Load testing scenarios

## Test Data

### ISS Pass API Integration
Tests use the Open Notify ISS Pass API as a real-world example:
```
URL: http://api.open-notify.org/iss-pass.json
Params: {"lat": 37.7749, "lon": -122.4194}  # San Francisco coordinates
```

This API provides:
- Predictable, stable responses for testing
- Geographic coordinate parameters for canonicalization testing
- JSON responses suitable for caching validation
- No authentication requirements

### Test Fixtures
- `cache_config` - Standard cache configuration
- `clean_cache_db` - Ensures clean test database
- `cache_instance` - MongoHTTPCache instance for testing
- `cached_client` - CachedHTTPClient instance for testing
- `sample_response` - Mock ISS API response data

## Running Tests

### Standard Test Commands
```bash
# All tests
uv run pytest
make test

# Fast tests only (excludes slow and network tests)
uv run pytest -m "not slow and not network"
make test-fast

# Network tests only (requires internet)
uv run pytest -m "network"
make test-network

# Slow tests only
uv run pytest -m "slow"
make test-slow

# Cache tests specifically
uv run pytest tests/test_http_cache.py
make test-cache

# Unit tests only
uv run pytest -m "unit"
make test-unit
```

### Test Categories by Mark
```bash
# Unit tests: Fast, no external dependencies
uv run pytest -m "unit"

# Integration tests: Multiple components, mocked externals
uv run pytest -m "integration"

# Network tests: Real API calls (skipped in CI)
uv run pytest -m "network"

# Slow tests: Performance/timing dependent
uv run pytest -m "slow"
```

## Test Status

### ✅ Working Tests
- **Unit Tests**: All RequestCanonicalizer tests pass
  - Coordinate rounding to specified precision
  - Date/time truncation to YYYY-MM-DD format
  - URL path coordinate canonicalization
  - Configuration-based behavior control

- **Basic Integration**: Cache initialization and key generation
  - MongoDB connection handling
  - Consistent cache key generation
  - Configuration validation

- **Error Handling**: Graceful degradation when MongoDB unavailable
  - Tests continue when database is not accessible
  - Proper error messages returned
  - No exceptions thrown for missing dependencies

### ⚠️ Known Issues
- **MongoDB DateTime Integration**: Timezone comparison issue
  - Error: "can't compare offset-naive and offset-aware datetimes"
  - Affects cache storage/retrieval tests requiring real MongoDB
  - Core caching logic is sound (unit tests pass)
  - Issue is in timezone handling between Python and MongoDB

### 🔧 Technical Debt
- Some tests marked as skipped when MongoDB unavailable rather than using integration test strategies
- Could benefit from more sophisticated mocking for MongoDB operations
- Network tests require manual execution for full validation

## Test Coverage

Current coverage focuses on:
- ✅ Input canonicalization (coordinates, dates)
- ✅ Cache key generation and consistency
- ✅ Error handling and graceful degradation
- ✅ Configuration validation
- ⚠️ End-to-end cache workflows (MongoDB timezone issue)
- 🔄 Network integration (manual testing required)

## Testing Best Practices Demonstrated

### LinkML Guidelines Implementation
1. **pytest Framework**: All new tests use pytest
2. **Test Organization**: Tests grouped by scope under tests/
3. **Small Fixtures**: Purpose-built test data rather than large datasets
4. **Pytest Marks**: Proper categorization with network/slow/unit/integration marks
5. **Environment Management**: Uses uv for dependency management
6. **CI Integration**: Excludes network tests in automated testing

### Testing Patterns
1. **Fixture-Based Setup**: Clean database setup/teardown
2. **Mock Strategies**: External service mocking for unit tests
3. **Parameterized Tests**: Multiple scenarios with single test functions
4. **Error Condition Testing**: Both success and failure paths
5. **Performance Testing**: Timing and load validation

### Code Quality
1. **Type Safety**: Full type annotations in test code
2. **Documentation**: Comprehensive docstrings explaining test purpose
3. **Maintainability**: Clear test structure and naming conventions
4. **Isolation**: Tests don't depend on each other or external state

## Example Test Run Output

```bash
$ make test-fast
Running fast tests...
=========================== test session starts ============================
collected 49 items / 5 deselected

tests/test_http_cache.py::TestRequestCanonicalizer::test_coordinate_rounding PASSED
tests/test_http_cache.py::TestRequestCanonicalizer::test_coordinate_variations PASSED
tests/test_http_cache.py::TestRequestCanonicalizer::test_datetime_truncation PASSED
...
================ 43 passed, 6 failed, 5 deselected in 37.75s ================
```

The testing framework successfully demonstrates:
- ✅ Core functionality validation
- ✅ Proper test categorization and filtering
- ✅ Real-world API integration patterns
- ✅ Comprehensive error handling
- ⚠️ Integration issues caught early (timezone bug)

This provides a solid foundation for maintaining high code quality while supporting rapid development iterations.
