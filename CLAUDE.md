# Claude Development Guidelines

This document establishes the development patterns and preferences for the biosample-enricher project. Follow these guidelines consistently across all development work.

## File Organization and Paths

### Path Resolution
- ALWAYS use centralized path utilities from `biosample_enricher.paths`
- NEVER use relative paths or hardcoded path chains like `parent.parent`
- Project-root relative paths for all data, logs, and config access
- Exception: Foundation utilities (`paths.py`, `conftest.py`) that establish project root

```python
# ✅ Good: Use centralized utilities
from biosample_enricher.paths import get_project_root, get_logs_dir, get_data_dir

log_file = get_logs_dir() / f"operation_{timestamp}.log"
output_file = get_data_dir() / "outputs" / "results.json"

# ❌ Bad: Hardcoded relative paths
log_file = Path(__file__).parent.parent / "logs" / "operation.log"
output_file = "../../data/outputs/results.json"
```

### Directory Structure Separation
- **logs/**: Operational logging with timestamped, meaningful filenames
- **data/**: Application data and outputs
- **config/**: Configuration files (YAML, etc.)
- **docs/**: Documentation (separate from operational files)
- **prompts/**: Operational prompt files (NOT documentation)

NEVER mix prompts with documentation. Prompts are operational files.

### Output Formats
- Prefer JSON summaries over redundant markdown files
- Use compact, structured data for metrics and statistics
- Generate markdown only when explicitly requested for human consumption

## CLI and Script Integration

### CLI Aliases
- ALWAYS define CLI aliases in `pyproject.toml` for runnable scripts
- Use CLI aliases in Makefile targets, NEVER module/file names
- Every meaningful script should have a CLI alias unless it's throwaway code

```toml
# pyproject.toml [project.scripts]
biosample-enricher = "biosample_enricher.cli:main"
soil-enricher = "biosample_enricher.soil_enricher:cli"
metrics-dashboard = "biosample_enricher.metrics.dashboard:cli"
```

```makefile
# ✅ Good: Use CLI aliases
soil-demo: install-dev
	uv run soil-enricher --demo-mode

# ❌ Bad: Use module names
soil-demo: install-dev
	uv run python -m biosample_enricher.soil_enricher
```

## Logging and Output

### Logging Configuration
- Default logs to `logs/` directory with meaningful, timestamped filenames
- Use structured logging from `biosample_enricher.logging_config`
- Include operation context in log filenames
- Replace all `print()`, `click.echo()`, and `console.print()` with logging
- Exception: CLI user interaction may use `click.echo()` for direct feedback

```python
# ✅ Good: Structured logging with context
from biosample_enricher.logging_config import get_logger
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/metrics_evaluation_{timestamp}.log"
logger = get_logger(__name__)
logger.info(f"Starting operation with {len(items)} items")

# ❌ Bad: Generic logging or print statements
import logging
logging.info("Starting operation")
print("Processing data...")  # Use logger.info() instead
click.echo("Status update")  # Use logger.info() instead (except for user interaction)
```

### File Naming Patterns
- Timestamped logs: `operation_YYYYMMDD_HHMMSS.log`
- Structured outputs: `results_summary.json` not `results.md`
- Backup files: Handled automatically by git attributes system

## Code Quality Standards

### Import Standards (Absolute Requirements)
- ALL imports at top of file, definitively - NO conditional imports
- NO try/except around imports - dependencies are either required or not used
- NO `HAS_X` style constants based on import success
- Handle optional functionality through runtime configuration, not import-time detection

### Type Safety (Absolute Requirements)
- Complete type annotations for all public functions and methods
- Use modern Python 3.10+ union syntax (`str | None` not `Optional[str]`)
- mypy strict mode compliance with minimal exceptions
- Avoid `# type: ignore`, `# noqa`, or suppressions except for:
  - Untyped third-party libraries without available type stubs
  - Must include explanatory comment when used

```python
# ✅ Good: Complete modern typing
def fetch_elevation_data(
    latitude: float,
    longitude: float,
    providers: list[str] | None = None,
    *,
    timeout_seconds: float = 30.0,
) -> list[Observation]:
    """Fetch elevation with complete type safety."""
    pass

# ❌ Bad: Missing types or old syntax
def fetch_elevation_data(latitude, longitude, providers=None):
    pass
```

### Quality Gates (Must Pass ALL)
All code must pass these checks before merge:
```bash
make check-ci  # This includes:
# - ruff linting and formatting
# - mypy type checking
# - deptry dependency validation
# - comprehensive test suite
```

NO exceptions, workarounds, or shortcuts allowed.

### Error Handling
- Explicit error handling for all external dependencies
- Graceful degradation when services unavailable
- Rich error context with logging

```python
# ✅ Good: Comprehensive error handling
try:
    response = await client.get(url, timeout=timeout_s)
    response.raise_for_status()
    return FetchResult(ok=True, data=response.json())
except httpx.TimeoutException as e:
    logger.error(f"API timeout after {timeout_s}s: {e}")
    return FetchResult(ok=False, error=f"Timeout after {timeout_s}s")
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error {e.response.status_code}: {e}")
    return FetchResult(ok=False, error=f"HTTP {e.response.status_code}")
```

## Testing Standards

### Test Organization
- pytest framework for all new tests
- Proper test categorization with marks:
  - `@pytest.mark.unit` - Fast, isolated, no external deps
  - `@pytest.mark.integration` - Multiple components, mocked externals
  - `@pytest.mark.network` - Real API calls (skipped in CI)
  - `@pytest.mark.slow` - Performance/timing tests

### Test Quality
- Comprehensive coverage with meaningful assertions
- Both positive and negative test cases
- Independent tests that can run in any order
- Purpose-built fixtures, not large datasets
- NEVER use mocks or patches - test against real implementations
- Use real services with graceful degradation when unavailable

## Performance and Architecture

### Async Patterns
- Use async/await for I/O operations
- Connection pooling for HTTP clients
- Semaphores for rate limiting
- Proper resource cleanup with context managers

### Caching Strategy
- Coordinate canonicalization for cache efficiency
- Smart cache keys with proper TTL
- Memory-efficient patterns with cleanup
- Git attributes backup system for precious files
- MongoDB primary, SQLite fallback - handle connection failures at runtime, not import time

### HTTP Library Standards
- **Primary HTTP**: Use `requests` + `requests-cache` through `biosample_enricher.http_cache`
- **Centralized caching**: ALL internet requests MUST go through `http_cache.py`
- **Coordinate canonicalization**: Automatic rounding to 4 decimal places for cache efficiency
- **No direct HTTP clients**: Never import `httpx`, `aiohttp`, `urllib.request` for making requests
- **URL manipulation**: `urllib.parse` is acceptable for URL encoding, parsing, validation
- **Third-party library HTTP**: Be aware some libraries (like `meteostat`) may bypass our cache

## Security Requirements

### API Key Management
**Supported APIs:**
- `GOOGLE_MAIN_API_KEY` - Single Google API key for all Google services (Maps, Places, Elevation, Geocoding)
- `OPENAI_API_KEY` - Reserved for future OpenAI integration (not currently implemented)

**API Key Standards:**
- Environment variables only (never hardcode)
- Single Google key for all Google services
- Handle missing keys at runtime through service initialization, not import time
- Validate API key formats without logging actual keys
- Graceful degradation when keys unavailable
- No credentials in logs or error messages

**Keyless Services (No API keys required):**
- Weather: MeteostatProvider, OpenMeteoProvider
- Elevation: USGS, Open Topo Data
- Marine: GEBCO, ESA CCI, NOAA
- All other public data providers

### Input Validation
- Comprehensive Pydantic models with validation
- Sanitize all external inputs
- Range validation for coordinates and numeric inputs
- Prevent injection attacks in file handling

## Build and CI/CD

### Development Tools
- `uv` for dependency management and script execution
- `ruff` for linting and formatting (Black-compatible)
- `mypy` for type checking
- `deptry` for dependency analysis

### Makefile Standards
- Clear target descriptions with `## comments`
- Use CLI aliases not module names
- Proper dependency chains
- Color output for user experience

## Data Management

### Backup System
- `.backups/` directory contains timestamped backups of precious LLM-generated files
- Managed by git attributes system with `filter=backup-precious`
- Use `git restore` and `.backups/` for recovery, not recreation

### File Formats
- JSON for structured data and summaries
- YAML for configuration files
- CSV for tabular exports
- Markdown only for human-readable documentation

## Documentation Philosophy

### Documentation Types
- **Technical docs** (`docs/`): Architecture, APIs, guidelines
- **Operational files** (`prompts/`, `config/`): Not documentation
- **Code comments**: Explain "why", not "what"
- **Docstrings**: Google-style with comprehensive information

### Documentation Quality
- Examples in all public APIs
- Error conditions documented
- Performance characteristics noted
- Security considerations included

---

## Enforcement

These guidelines are enforced through:
1. **Automated tooling**: CI/CD pipeline blocks non-compliant code
2. **Code review**: Human verification of patterns and architecture
3. **Documentation**: This file serves as the source of truth

**Remember**: These are not suggestions - they are requirements. Follow them consistently to maintain code quality, security, and maintainability across the entire project.
