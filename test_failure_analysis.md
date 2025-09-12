# Test Failure Analysis for GPT-5 Deep Research

## Problem Summary

All 155 tests pass individually and in quiet mode (`pytest tests/ -q`), but 18 specific tests fail consistently when run in verbose mode (`pytest tests/ -v --durations=0`) as part of the full test suite. This is a test execution order/environment interference issue that only manifests under specific pytest execution conditions.

## Test Execution Results

- ✅ **Individual tests**: All 155 tests pass when run individually
- ✅ **Quiet mode**: All 155 tests pass with `pytest tests/ -q`
- ❌ **Verbose mode**: 18 tests fail with `pytest tests/ -v --durations=0`
- ❌ **Make check-ci**: 18 tests fail with `make check-ci` (uses verbose mode)

## Failing Test Pattern

All 18 failing tests are Google API related:
- `tests/test_elevation.py::TestElevationProviders::test_google_provider_live`
- `tests/test_elevation.py::TestElevationEndToEnd::test_full_service_*`
- `tests/test_elevation_cli.py::TestElevationCLI::test_lookup_*`
- `tests/test_google_apis.py::TestGoogleAPIsIntegration::test_*`
- `tests/test_reverse_geocoding.py::TestGoogleReverseGeocodingProvider::test_*`

## Root Cause Analysis

### Primary Issue: Environment Variable Corruption
- Google API key is valid and present in `.env` file: `GOOGLE_MAIN_API_KEY="[REDACTED]"`
- Error message in failing tests: `"The provided API key is invalid."`
- Tests that modify environment variables are interfering with subsequent tests

### Suspected Interference Source
File: `tests/test_logging.py`, line 101:
```python
@patch.dict(os.environ, {}, clear=True)
def test_configure_from_env_defaults(self):
```

This decorator clears ALL environment variables, including `GOOGLE_MAIN_API_KEY`, affecting tests that run after it in verbose mode execution order.

### Verbose Mode Timing Issue
- Verbose mode (`-v --durations=0`) changes test execution timing/order
- Environment modifications in one test affect subsequent tests
- HTTP cache may be preserving invalid API responses between test runs

## Environment Configuration Architecture

### Current .env Loading Strategy
- `biosample_enricher/config.py`: Loads `.env` at module import time
- `tests/conftest.py`: Loads `.env` during pytest configuration
- Multiple modules attempt to load `.env` independently

### Configuration Caching
- `@lru_cache` decorators in `config.py` cache configuration values
- Cache clearing mechanism exists but may not be sufficient for test isolation

## Attempted Solutions and Results

### 1. Cache Clearing Approach ❌
- Added `clear_config_cache()` function
- Added auto-clearing fixtures in `conftest.py`
- Added teardown methods in `test_logging.py`
- **Result**: Did not resolve the issue

### 2. Frequent .env Loading ❌
- Modified `get_api_key()` to call `load_dotenv()` on every invocation
- Added `.env` loading to Google provider constructors
- **Result**: Did not resolve the issue

### 3. Environment Preservation ❌
- Modified `@patch.dict` to preserve `GOOGLE_MAIN_API_KEY`
- Hardcoded the API key value in the patch
- **Result**: Did not resolve the issue

### 4. Test Execution Control ❌
- Added `--maxfail=1` to stop at first failure
- Modified test execution order
- **Result**: Confirmed first failure but didn't fix underlying issue

## Technical Environment

- Python 3.11.12
- pytest 8.4.2
- Environment loading: `python-dotenv` package
- Caching: `requests-cache` with MongoDB/SQLite backend
- Test configuration: `pyproject.toml` with coverage and pytest options

## Key Observations

1. **Timing Dependency**: Issue only appears with verbose output flags
2. **Order Dependency**: Tests pass individually but fail in suite execution
3. **API Key Validity**: Key is valid (individual tests prove this)
4. **Environment Isolation**: Tests are not properly isolated from each other
5. **Cache Interference**: HTTP cache may be preserving invalid responses

## Makefile Test Configuration

Current test command:
```makefile
test: ## Run tests with timing
	@echo "Running tests with timing..."
	uv run pytest tests/ -v --durations=0
```

## Research Questions for GPT-5

1. **Why does pytest verbose mode change test execution in a way that affects environment variable loading?**

2. **How can we ensure complete test isolation when using `@patch.dict(os.environ, {}, clear=True)` without affecting subsequent tests?**

3. **What is the most robust pattern for loading `.env` files in pytest suites where some tests modify the environment?**

4. **Is there a pytest plugin or configuration that can ensure environment variables are restored between tests automatically?**

5. **Could the `requests-cache` HTTP caching be preserving invalid API responses across test runs, and how can this be prevented without clearing cache every time?**

6. **What pytest execution model differences exist between quiet mode (`-q`) and verbose mode (`-v --durations=0`) that could cause this behavior?**

## Success Criteria

The solution must ensure:
- All 155 tests pass with `make test` (verbose mode with timing)
- All 155 tests pass with `make check-ci` 
- No test failures regardless of pytest flags used
- Preserve HTTP cache performance (don't clear cache every run)
- Maintain current test architecture and minimal code changes

## Code Repository Context

- Repository: biosample-enricher
- Main configuration: `biosample_enricher/config.py`
- Test configuration: `tests/conftest.py`
- Failing test files: Google API related tests
- Environment file: `.env` with valid API keys
- Build system: Uses `uv` package manager and Makefile

The fundamental issue is test isolation failure in pytest's verbose execution mode, specifically around environment variable management for Google API authentication.