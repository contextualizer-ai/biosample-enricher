# Contributing to Biosample Enricher

Thank you for your interest in contributing to Biosample Enricher! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Adding New Features](#adding-new-features)
- [Documentation](#documentation)
- [Getting Help](#getting-help)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [UV package manager](https://github.com/astral-sh/uv) (recommended)
- Git
- GitHub account

### Finding an Issue

1. Browse [open issues](https://github.com/contextualizer-ai/biosample-enricher/issues)
2. Look for issues tagged with `good first issue` for beginner-friendly tasks
3. Comment on the issue to let others know you're working on it
4. If you have a new idea, open an issue first to discuss it

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/biosample-enricher.git
cd biosample-enricher
```

### 2. Set Up Development Environment

```bash
# Complete development setup (installs all dependencies and pre-commit hooks)
make dev-setup
```

This command:
- Installs UV if not present
- Syncs all dependencies (including dev dependencies)
- Installs pre-commit hooks

### 3. Verify Installation

```bash
# Run fast tests to verify setup
make test-fast

# Check code quality
make dev-check
```

## Development Workflow

### Branch Naming

Use descriptive branch names with issue numbers:

```bash
git checkout -b 123-add-air-quality-provider
git checkout -b 145-move-demo-files
git checkout -b 152-add-docstring-examples
```

### Making Changes

1. **Create a feature branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b your-branch-name
   ```

2. **Make your changes** following our [Code Standards](#code-standards)

3. **Test your changes**:
   ```bash
   # Run fast tests (unit + integration, no network)
   make test-fast

   # Run all quality checks
   make dev-check
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes

   - Detailed bullet points
   - Explaining the changes

   Closes #123"
   ```

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit:

- **backup-precious**: Backs up LLM-generated files
- **trim-trailing-whitespace**: Removes trailing whitespace
- **fix-end-of-files**: Ensures files end with newline
- **check-merge-conflicts**: Prevents merge conflict markers
- **check-case-conflicts**: Prevents case-sensitive filename issues
- **check-json**: Validates JSON files
- **check-yaml**: Validates YAML files
- **ruff-format**: Auto-formats Python code
- **ruff**: Lints Python code
- **mypy**: Type checks Python code

If hooks fail, fix the issues and commit again.

## Code Standards

### Python Style

We follow strict code quality standards enforced by automated tools:

#### Type Annotations (Required)

```python
# ✅ Good: Complete type annotations
def fetch_elevation_data(
    latitude: float,
    longitude: float,
    providers: list[str] | None = None,
    *,
    timeout_seconds: float = 30.0,
) -> list[Observation]:
    """Fetch elevation with complete type safety."""
    pass

# ❌ Bad: Missing types
def fetch_elevation_data(latitude, longitude, providers=None):
    pass
```

- Use modern Python 3.10+ union syntax: `str | None` instead of `Optional[str]`
- Full type hints for all public functions and methods
- mypy strict mode compliance

#### Import Standards (Absolute Requirement)

```python
# ✅ Good: All imports at top
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from biosample_enricher.models import Observation

# ❌ Bad: Conditional imports
try:
    import optional_package
    HAS_OPTIONAL = True
except ImportError:
    HAS_OPTIONAL = False
```

- ALL imports at top of file
- NO conditional imports or try/except around imports
- Handle optional functionality through runtime configuration

#### Path Resolution

```python
# ✅ Good: Use centralized utilities
from biosample_enricher.paths import get_project_root, get_logs_dir

log_file = get_logs_dir() / f"operation_{timestamp}.log"

# ❌ Bad: Hardcoded relative paths
log_file = Path(__file__).parent.parent / "logs" / "operation.log"
```

#### Error Handling

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

### Logging Standards

```python
# ✅ Good: Structured logging
from biosample_enricher.logging_config import get_logger
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/operation_{timestamp}.log"
logger = get_logger(__name__)
logger.info(f"Starting operation with {len(items)} items")

# ❌ Bad: Print statements
print("Processing data...")  # Use logger.info() instead
click.echo("Status update")  # Use logger.info() (except for CLI user interaction)
```

### CLI Standards

```python
# ✅ Good: Use @click.option for all parameters
@click.command()
@click.option("--lat", type=float, required=True, help="Latitude in decimal degrees")
@click.option("--lon", type=float, required=True, help="Longitude in decimal degrees")
def lookup(lat: float, lon: float) -> None:
    """Lookup elevation for coordinates."""
    pass

# ❌ Bad: Use @click.argument
@click.command()
@click.argument("lat", type=float)
@click.argument("lon", type=float)
def lookup(lat: float, lon: float) -> None:
    pass
```

### Configuration Management

```python
# ✅ Good: Runtime configuration loading
from biosample_enricher.host_detector import get_host_detector
detector = get_host_detector()  # Loads from config/host_detection.yaml

# ❌ Bad: Hardcoded configuration
HOST_KEYWORDS = ["gut", "rhizosphere", "clinical"]  # Should be in YAML
```

## Testing Guidelines

### Test Organization

Tests are organized by type using pytest marks:

```python
import pytest

@pytest.mark.unit
def test_coordinate_validation():
    """Test coordinate validation logic."""
    pass

@pytest.mark.integration
def test_service_integration():
    """Test multiple components together."""
    pass

@pytest.mark.network
def test_api_call():
    """Test real API calls (skipped in CI)."""
    pass

@pytest.mark.slow
def test_performance():
    """Test performance/timing."""
    pass
```

### Running Tests

```bash
# Fast tests only (unit + integration, no network/slow)
make test-fast

# All tests with coverage
make test-cov

# Specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests
```

### Writing Tests

```python
# ✅ Good: Clear test with meaningful assertions
def test_elevation_service_returns_observations():
    """Test that ElevationService returns observations for valid coordinates."""
    service = ElevationService()
    request = ElevationRequest(latitude=40.7128, longitude=-74.0060)

    observations = service.get_elevation(request)

    assert len(observations) > 0
    assert all(obs.variable == Variable.ELEVATION for obs in observations)
    assert any(obs.value_numeric is not None for obs in observations)

# ❌ Bad: Unclear test without proper assertions
def test_elevation():
    service = ElevationService()
    result = service.get_elevation(ElevationRequest(40, -74))
    assert result
```

### Test Quality Requirements

- **No mocks or patches** - Test against real implementations
- **Independent tests** - Tests should run in any order
- **Purpose-built fixtures** - Not large datasets
- **Comprehensive coverage** - Both positive and negative cases

## Submitting Changes

### Pull Request Process

1. **Push your branch** to your fork:
   ```bash
   git push origin your-branch-name
   ```

2. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Reference the issue number (e.g., "Closes #123")
   - Fill out the PR template
   - **Apply appropriate labels** for release notes (see below)
   - Include test results if applicable

3. **PR Labels for Release Notes**:

   Apply labels to categorize your PR in auto-generated release notes:

   - `breaking-change`: Breaking API changes
   - `feature` or `enhancement`: New features
   - `bug` or `fix`: Bug fixes
   - `documentation` or `docs`: Documentation updates
   - `testing` or `tests`: Test improvements
   - `ci` or `infrastructure`: CI/CD changes
   - `maintenance` or `refactor`: Code maintenance
   - `dependencies`: Dependency updates
   - `ignore-for-release`: Internal changes not user-facing

4. **CI Checks**: All PRs must pass:
   - Ruff formatting
   - Ruff linting
   - mypy type checking
   - deptry dependency validation
   - pytest test suite

5. **Code Review**: Address feedback from reviewers

6. **Merge**: Maintainers will merge when approved

### Git Commit Guidelines

```bash
# ✅ Good commit message
git commit -m "Add air quality provider with AirNow and OpenAQ

- Implement AirNowProvider for US coverage
- Implement OpenAQProvider for global coverage
- Add AirQualityService with multi-provider support
- Include comprehensive tests for both providers
- Add CLI command for air quality lookups

Closes #125"

# ❌ Bad commit message
git commit -m "fixes"
```

## Adding New Features

### Adding a New Provider

1. **Create provider directory** structure:
   ```
   biosample_enricher/
   └── new_domain/
       ├── __init__.py
       ├── service.py
       ├── models.py
       └── providers/
           ├── __init__.py
           ├── provider_one.py
           └── provider_two.py
   ```

2. **Implement models** (Pydantic):
   ```python
   from pydantic import BaseModel, Field

   class DomainObservation(BaseModel):
       """Observation from domain provider."""
       value: float
       unit: str
       quality_score: float = Field(ge=0, le=100)
   ```

3. **Implement providers**:
   ```python
   from biosample_enricher.http_cache import get_cached_session

   class ProviderOne:
       """Provider implementation."""

       def fetch_data(self, lat: float, lon: float) -> DomainObservation:
           """Fetch data from provider."""
           session = get_cached_session()
           # Construct 'url' and 'params' according to the provider's API requirements
           response = session.get(url, params=params)
           # Process response
           return DomainObservation(...)
   ```

4. **Implement service**:
   ```python
   class DomainService:
       """Multi-provider domain service."""

       def __init__(self) -> None:
           self.providers = {
               "provider_one": ProviderOne(),
               "provider_two": ProviderTwo(),
           }

       def enrich_location(self, latitude: float, longitude: float) -> DomainResult:
           """Enrich location with domain data."""
           # Implement provider cascade logic
           pass
   ```

5. **Add CLI** (optional):
   ```python
   @click.group()
   def domain() -> None:
       """Domain enrichment commands."""
       pass

   @domain.command()
   @click.option("--lat", type=float, required=True)
   @click.option("--lon", type=float, required=True)
   def lookup(lat: float, lon: float) -> None:
       """Lookup domain data for coordinates."""
       service = DomainService()
       result = service.enrich_location(lat, lon)
       # Display results
   ```

6. **Add tests**:
   ```python
   @pytest.mark.unit
   def test_provider_one_success():
       """Test ProviderOne successful data fetch."""
       pass

   @pytest.mark.integration
   def test_domain_service_cascade():
       """Test DomainService provider cascade."""
       pass
   ```

7. **Update exports** in `biosample_enricher/__init__.py`:
   ```python
   from biosample_enricher.new_domain.service import DomainService

   __all__ = [
       # ... existing exports
       "DomainService",
   ]
   ```

8. **Add CLI alias** in `pyproject.toml`:
   ```toml
   [project.scripts]
   domain-enricher = "biosample_enricher.cli_domain:domain"
   ```

### Project Architecture Patterns

- **Service-based architecture**: Independent services with focused responsibilities
- **Multi-provider support**: Automatic fallback between data providers
- **Type safety**: Full Pydantic validation and mypy checking
- **Smart caching**: HTTP caching with coordinate canonicalization
- **Click-based CLIs**: Consistent CLI patterns across services

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def fetch_data(
    latitude: float,
    longitude: float,
    timeout_s: float = 30.0,
) -> list[Observation]:
    """Fetch data from multiple providers.

    Args:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        timeout_s: Request timeout in seconds

    Returns:
        List of observations from all providers

    Raises:
        ValueError: If coordinates are out of valid range
        TimeoutError: If request exceeds timeout

    Example:
        >>> service = DataService()
        >>> obs = service.fetch_data(40.7128, -74.0060)
        >>> print(f"Got {len(obs)} observations")
    """
    pass
```

### README Updates

When adding significant features, update README.md with:
- Service description
- API example
- CLI example
- Provider information

## Release Process (Maintainers)

### Creating a Release

1. **Ensure all PRs have appropriate labels** for release notes categorization

2. **Create and push a version tag**:
   ```bash
   # Create annotated tag following semantic versioning
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

3. **GitHub will automatically**:
   - Generate release notes from labeled PRs (via `.github/release.yml`)
   - Categorize changes by type
   - Link to PRs and credit contributors

4. **Create the GitHub Release**:
   - Go to GitHub Releases page
   - Click "Draft a new release"
   - Select the pushed tag
   - Click "Generate release notes" (auto-populated from PRs)
   - Review and edit if needed
   - Publish release

5. **Update CHANGELOG.md** (see #154):
   - Sync release notes to CHANGELOG.md
   - Maintain cumulative history

### Release Note Categories

PRs are automatically categorized based on labels:
- 🚨 **Breaking Changes**: `breaking-change`, `breaking`
- 🎉 **New Features**: `enhancement`, `feature`, `new-feature`
- 🐛 **Bug Fixes**: `bug`, `fix`, `bugfix`
- 📚 **Documentation**: `documentation`, `docs`
- 🧪 **Testing**: `testing`, `tests`
- 🏗️ **Infrastructure**: `ci`, `infrastructure`, `github-actions`
- 🔧 **Maintenance**: `maintenance`, `chore`, `refactor`
- 📦 **Dependencies**: `dependencies`, `deps`

PRs with `ignore-for-release` or `github-actions` labels are excluded.

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (v1.0.0 → v2.0.0): Breaking changes
- **MINOR** (v0.1.0 → v0.2.0): New features (backward compatible)
- **PATCH** (v0.1.0 → v0.1.1): Bug fixes (backward compatible)

## Getting Help

- **GitHub Issues**: [Open an issue](https://github.com/contextualizer-ai/biosample-enricher/issues)
- **GitHub Discussions**: For questions and general discussion
- **Email**: info@contextualizer.ai

## Development Resources

- **Project Guidelines**: See [CLAUDE.md](CLAUDE.md) for detailed development patterns
- **Makefile Commands**: Run `make help` to see all available commands
- **API Documentation**: See README.md for service APIs
- **Issue Tracker**: Browse issues for feature ideas and bugs

## License

By contributing to Biosample Enricher, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Biosample Enricher! 🎉
