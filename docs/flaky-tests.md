# Flaky Test Management

## Overview

"Flaky tests" are tests that sometimes pass and sometimes fail, even when the code hasn't changed. In our codebase, flaky tests are primarily caused by:

1. **External service timeouts** (USGS elevation API, Google APIs)
2. **Network connectivity issues**
3. **Rate limiting from third-party APIs**
4. **Temporary service outages**

## Our Strategy

### 1. Identification
Tests prone to flakiness are marked with `@pytest.mark.flaky(reruns=2, reruns_delay=10)`:
- **reruns=2**: Retry up to 2 times (3 total attempts)
- **reruns_delay=10**: Wait 10 seconds between retries

### 2. Current Flaky Tests

**USGS Elevation Provider Tests:**
- `test_usgs_provider_live`: Gateway timeouts (504 errors)
- `test_usgs_provider_ocean_location`: Service unavailability

**Potential Future Flaky Tests:**
- Google API tests (rate limiting)
- OSM/Nominatim tests (service limits)
- MongoDB connection tests (when using remote databases)

### 3. What Happens When Tests Fail

1. **First failure**: Test runs normally, fails due to timeout/network
2. **Wait period**: 10-second delay to allow service recovery
3. **Retry 1**: Test runs again with fresh connection
4. **If still failing**: Another 10-second delay
5. **Retry 2**: Final attempt
6. **Final failure**: If all 3 attempts fail, test is marked as FAILED

### 4. Dependencies

**pytest-rerunfailures**: Added to dev dependencies for retry functionality
```toml
dev = [
    "pytest-rerunfailures>=14.0",
    # ... other deps
]
```

### 5. Usage in CI

GitHub Actions will:
- Install pytest-rerunfailures automatically
- Retry flaky tests with delays
- Only fail builds if ALL retry attempts fail
- Report retry statistics in test output

### 6. Local Development

Run tests with flaky handling:
```bash
# Normal test run (includes retries for flaky tests)
make test

# Run only integration tests (includes flaky ones)
uv run pytest tests/ -m integration

# Skip flaky tests entirely
uv run pytest tests/ -m "not flaky"

# Run only flaky tests to debug them
uv run pytest tests/ -m flaky
```

### 7. When to Mark Tests as Flaky

Mark a test as flaky when:
- ✅ Failures are due to external service issues (timeouts, 503/504 errors)
- ✅ Test logic is correct but service is intermittently unavailable
- ✅ Failures are not reproducible locally with good network

Don't mark as flaky when:
- ❌ Test has logical bugs
- ❌ API credentials are missing
- ❌ Code behavior is actually incorrect
- ❌ Test assertions are wrong

### 8. Monitoring Flaky Tests

If flaky tests consistently fail even with retries:
1. Check service status (USGS, Google, etc.)
2. Verify API endpoints haven't changed
3. Consider increasing timeout values
4. Update test expectations for new error messages
5. Report issues to external service providers

### 9. Alternative Strategies

If retries aren't sufficient:
1. **Mock external services** in CI (not integration tests)
2. **Conditional skipping** based on service health checks
3. **Separate test suites** for external vs internal tests
4. **Service health monitoring** before running tests
