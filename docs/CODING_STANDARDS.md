# Coding Standards and Development Guidelines

This document establishes comprehensive coding standards for the biosample-enricher project, covering Python code, build systems, CI/CD, and project configuration.

## Table of Contents

1. [General Philosophy](#general-philosophy)
2. [Python Code Standards](#python-code-standards)
3. [Type Annotations](#type-annotations)
4. [Testing Standards](#testing-standards)
5. [Error Handling](#error-handling)
6. [Documentation Standards](#documentation-standards)
7. [Git and Version Control](#git-and-version-control)
8. [Build System (Makefile)](#build-system-makefile)
9. [Project Configuration (pyproject.toml)](#project-configuration-pyprojecttoml)
10. [GitHub Actions and CI/CD](#github-actions-and-cicd)
11. [Dependencies and Environment](#dependencies-and-environment)
12. [Security Standards](#security-standards)
13. [Performance Guidelines](#performance-guidelines)
14. [Code Review Guidelines](#code-review-guidelines)

## General Philosophy

### Core Principles

1. **Correctness First**: Code must be correct before being optimized
2. **Explicit is Better Than Implicit**: Follow Python's Zen
3. **No Suppressions**: Never use `# noqa`, `# type: ignore`, or similar workarounds
4. **Fail Fast**: Prefer early validation and clear error messages
5. **Defensive Programming**: Validate inputs, handle edge cases
6. **Consistent Patterns**: Follow established patterns in the codebase

### Quality Gates

All code must pass ALL of the following before being merged:

```bash
make check-ci  # This must pass completely
```

Which includes:
- ✅ Linting (ruff)
- ✅ Formatting (ruff format)
- ✅ Type checking (mypy)
- ✅ Dependency validation (deptry)
- ✅ All tests passing

## Python Code Standards

### Code Style and Formatting

**Formatter**: Use `ruff format` (Black-compatible)

```python
# ✅ Good: Proper formatting
def fetch_elevation(
    lat: float,
    lon: float,
    *,
    read_from_cache: bool = True,
    timeout_s: float = 30.0,
) -> ElevationResult:
    """Fetch elevation data with caching support."""
    pass

# ❌ Bad: Poor formatting
def fetch_elevation(lat:float,lon:float,read_from_cache:bool=True)->ElevationResult:
    pass
```

**Line Length**: 88 characters (ruff/Black default)

**Imports**: Follow PEP 8 ordering with ruff enforcement

```python
# ✅ Good: Proper import ordering
import os
import sys
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel

from .models import ElevationRequest
from .utils import calculate_distance
```

### Naming Conventions

```python
# ✅ Good: Clear, descriptive names
class ElevationService:
    """Service for fetching elevation data from multiple providers."""
    
    def __init__(self, google_api_key: str | None = None) -> None:
        self.google_api_key = google_api_key
        self._providers: dict[str, ElevationProvider] = {}
    
    async def get_elevation_for_coordinates(
        self, latitude: float, longitude: float
    ) -> list[Observation]:
        """Get elevation observations from all available providers."""
        pass

# ❌ Bad: Unclear, abbreviated names
class ElSvc:
    def __init__(self, key=None):
        self.key = key
        self.provs = {}
    
    async def get_elev(self, lat, lon):
        pass
```

**Naming Rules**:
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Variables: `snake_case`
- Constants: `SCREAMING_SNAKE_CASE`
- Private attributes: `_leading_underscore`
- Type variables: `PascalCase` (e.g., `TypeVar('T')`)

### Function and Class Design

```python
# ✅ Good: Single responsibility, clear interface
async def fetch_elevation_from_usgs(
    latitude: float,
    longitude: float,
    *,
    timeout_s: float = 30.0,
    read_from_cache: bool = True,
) -> FetchResult:
    """
    Fetch elevation data from USGS EPQS service.
    
    Args:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        timeout_s: Request timeout in seconds
        read_from_cache: Whether to use cached results
    
    Returns:
        FetchResult with elevation data or error information
        
    Raises:
        ValueError: If coordinates are invalid
        httpx.TimeoutException: If request times out
    """
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude}")
    
    # Implementation here
    pass

# ❌ Bad: Multiple responsibilities, unclear interface
def process_stuff(data, opts=None):
    # Does too many things, unclear what it returns
    pass
```

### Exception Handling

```python
# ✅ Good: Specific exceptions, clear error context
try:
    response = await client.get(url, timeout=timeout_s)
    response.raise_for_status()
    data = response.json()
except httpx.TimeoutException as e:
    logger.error(f"USGS API timeout after {timeout_s}s: {e}")
    return FetchResult(ok=False, error=f"Request timeout after {timeout_s}s")
except httpx.HTTPStatusError as e:
    logger.error(f"USGS API HTTP error {e.response.status_code}: {e}")
    return FetchResult(ok=False, error=f"HTTP {e.response.status_code}")
except ValueError as e:
    logger.error(f"USGS API returned invalid JSON: {e}")
    return FetchResult(ok=False, error="Invalid response format")

# ❌ Bad: Bare except, no context
try:
    response = get_data()
    return response.json()
except:
    return None
```

### Logging Standards

```python
# ✅ Good: Structured logging with context
from .logging_config import get_logger

logger = get_logger(__name__)

async def fetch_elevation(lat: float, lon: float) -> FetchResult:
    """Fetch elevation with proper logging."""
    logger.debug(f"Fetching elevation for {lat:.6f}, {lon:.6f}")
    
    try:
        result = await provider.fetch(lat, lon)
        if result.ok:
            logger.info(f"Successfully fetched elevation: {result.elevation}m")
        else:
            logger.warning(f"Elevation fetch failed: {result.error}")
        return result
    except Exception as e:
        logger.error(f"Unexpected error fetching elevation: {e}", exc_info=True)
        raise

# ❌ Bad: Print statements, no context
def fetch_elevation(lat, lon):
    print(f"Getting elevation for {lat}, {lon}")
    try:
        return get_data()
    except Exception as e:
        print("Error:", e)
        return None
```

## Type Annotations

### Comprehensive Type Coverage

**Required**: All public functions, methods, and class attributes must have type annotations.

```python
# ✅ Good: Complete type annotations
from typing import Any, Protocol
from collections.abc import Awaitable

class ElevationProvider(Protocol):
    """Protocol for elevation data providers."""
    
    name: str
    endpoint: str
    
    async def fetch(
        self, 
        lat: float, 
        lon: float,
        *,
        timeout_s: float = 30.0,
    ) -> FetchResult:
        """Fetch elevation data."""
        ...

class USGSProvider:
    """USGS elevation provider implementation."""
    
    def __init__(self, endpoint: str = "https://epqs.nationalmap.gov/v1/json") -> None:
        self.name: str = "usgs_epqs"
        self.endpoint: str = endpoint
        self._session: httpx.AsyncClient | None = None

    async def fetch(
        self, 
        lat: float, 
        lon: float,
        *,
        timeout_s: float = 30.0,
    ) -> FetchResult:
        """Implementation of elevation fetch."""
        pass

# ❌ Bad: Missing type annotations
class USGSProvider:
    def __init__(self, endpoint="https://epqs.nationalmap.gov/v1/json"):
        self.name = "usgs_epqs"
        self.endpoint = endpoint
    
    async def fetch(self, lat, lon, timeout_s=30.0):
        pass
```

### Modern Type Syntax

Use Python 3.10+ union syntax and generics:

```python
# ✅ Good: Modern Python 3.10+ syntax
def process_coordinates(
    coords: list[tuple[float, float]] | None = None
) -> dict[str, Any]:
    """Process coordinate list."""
    pass

def get_providers() -> dict[str, ElevationProvider]:
    """Get available providers."""
    pass

# ❌ Bad: Old-style typing
from typing import Dict, List, Optional, Tuple, Union

def process_coordinates(
    coords: Optional[List[Tuple[float, float]]] = None
) -> Dict[str, Any]:
    pass
```

### Pydantic Models

```python
# ✅ Good: Comprehensive Pydantic model
from pydantic import BaseModel, Field, field_validator

class ElevationRequest(BaseModel):
    """Request for elevation data at specific coordinates."""
    
    latitude: float = Field(
        ge=-90, 
        le=90, 
        description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ge=-180, 
        le=180, 
        description="Longitude in decimal degrees"
    )
    preferred_providers: list[str] | None = Field(
        default=None, 
        description="Preferred providers in order of preference"
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
        description="Request timeout in seconds"
    )
    
    @field_validator('preferred_providers')
    @classmethod
    def validate_providers(cls, v: list[str] | None) -> list[str] | None:
        """Validate provider names."""
        if v is None:
            return v
        
        valid_providers = {"usgs", "google", "osm", "open_topo_data"}
        invalid = set(v) - valid_providers
        if invalid:
            raise ValueError(f"Invalid providers: {invalid}")
        return v

# ❌ Bad: Minimal validation
class ElevationRequest(BaseModel):
    latitude: float
    longitude: float
    providers: list[str] = []
```

## Testing Standards

### Test Structure and Organization

```python
# ✅ Good: Well-organized test class
import pytest
from unittest.mock import AsyncMock, Mock

from biosample_enricher.elevation import ElevationService, USGSProvider
from biosample_enricher.models import ElevationRequest, FetchResult

class TestUSGSProvider:
    """Test USGS elevation provider."""
    
    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.provider = USGSProvider()
    
    @pytest.mark.asyncio
    async def test_fetch_valid_coordinates_success(self) -> None:
        """Test successful elevation fetch with valid coordinates."""
        # Arrange
        lat, lon = 37.7749, -122.4194  # San Francisco
        
        # Act
        result = await self.provider.fetch(lat, lon, timeout_s=30.0)
        
        # Assert
        assert result.ok is True
        assert result.elevation is not None
        assert isinstance(result.elevation, float)
        assert result.elevation > -100  # Reasonable elevation range
        assert result.location is not None
        assert abs(result.location.lat - lat) < 0.01
        assert abs(result.location.lon - lon) < 0.01
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_coordinates_raises_error(self) -> None:
        """Test that invalid coordinates raise appropriate errors."""
        # Test invalid latitude
        with pytest.raises(ValueError, match="Invalid latitude"):
            await self.provider.fetch(91.0, 0.0)  # > 90 degrees
            
        with pytest.raises(ValueError, match="Invalid latitude"):
            await self.provider.fetch(-91.0, 0.0)  # < -90 degrees
        
        # Test invalid longitude
        with pytest.raises(ValueError, match="Invalid longitude"):
            await self.provider.fetch(0.0, 181.0)  # > 180 degrees

    @pytest.mark.asyncio
    async def test_fetch_ocean_location_returns_error(self) -> None:
        """Test that ocean locations return appropriate error."""
        # Pacific Ocean
        result = await self.provider.fetch(30.0, -140.0, timeout_s=30.0)
        
        assert result.ok is False
        assert "no data" in result.error.lower() or "no elevation" in result.error.lower()

# ❌ Bad: Poor test organization
def test_usgs():
    provider = USGSProvider()
    result = provider.fetch(37.7749, -122.4194)
    assert result  # Vague assertion
```

### Test Coverage Requirements

- **Minimum**: 80% line coverage for new code
- **Target**: 90% line coverage for core business logic
- **Required**: 100% coverage for critical paths (error handling, validation)

### Testing Environment

```python
# tests/conftest.py - ✅ Good: Proper test configuration
import os
from pathlib import Path
import pytest
from dotenv import load_dotenv

def pytest_configure(config):
    """Configure pytest session - load environment variables."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

@pytest.fixture(scope="session")
def elevation_service():
    """Provide elevation service for tests."""
    from biosample_enricher.elevation import ElevationService
    return ElevationService.from_env()

@pytest.fixture
def sample_coordinates():
    """Provide sample coordinates for testing."""
    return [
        (37.7749, -122.4194),  # San Francisco
        (40.7128, -74.0060),   # New York
        (51.5074, -0.1278),    # London
    ]
```

## Error Handling

### Error Hierarchies

```python
# ✅ Good: Clear error hierarchy
class BiosampleEnricherError(Exception):
    """Base exception for biosample enricher."""
    pass

class ValidationError(BiosampleEnricherError):
    """Raised when data validation fails."""
    pass

class ProviderError(BiosampleEnricherError):
    """Raised when external provider fails."""
    
    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"{provider}: {message}")

class CoordinateValidationError(ValidationError):
    """Raised when coordinates are invalid."""
    
    def __init__(self, latitude: float | None = None, longitude: float | None = None):
        self.latitude = latitude
        self.longitude = longitude
        
        if latitude is not None and not (-90 <= latitude <= 90):
            message = f"Invalid latitude: {latitude} (must be -90 to 90)"
        elif longitude is not None and not (-180 <= longitude <= 180):
            message = f"Invalid longitude: {longitude} (must be -180 to 180)"
        else:
            message = "Invalid coordinates"
        
        super().__init__(message)
```

### Error Context and Recovery

```python
# ✅ Good: Rich error context and recovery strategies
async def fetch_elevation_with_fallback(
    request: ElevationRequest,
) -> list[Observation]:
    """Fetch elevation with automatic fallback between providers."""
    observations = []
    errors = []
    
    for provider in self.get_providers_for_location(request.latitude, request.longitude):
        try:
            result = await provider.fetch(
                request.latitude, 
                request.longitude,
                timeout_s=request.timeout_seconds,
            )
            
            observation = self._create_observation(request, provider, result)
            observations.append(observation)
            
            if result.ok:
                logger.debug(f"Successfully fetched from {provider.name}")
            else:
                logger.warning(f"Provider {provider.name} returned error: {result.error}")
                
        except Exception as e:
            error_context = {
                "provider": provider.name,
                "coordinates": (request.latitude, request.longitude),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            errors.append(error_context)
            logger.error(f"Provider {provider.name} failed: {e}", extra=error_context)
            
            # Create error observation for tracking
            error_obs = self._create_error_observation(request, provider, str(e))
            observations.append(error_obs)
    
    if not any(obs.value_status == ValueStatus.OK for obs in observations):
        logger.error(f"All providers failed for {request.latitude}, {request.longitude}")
        # Still return observations with error details rather than raising
    
    return observations
```

## Documentation Standards

### Docstring Format

Use Google-style docstrings with comprehensive information:

```python
# ✅ Good: Comprehensive docstring
async def fetch_elevation_data(
    latitude: float,
    longitude: float,
    providers: list[str] | None = None,
    *,
    timeout_seconds: float = 30.0,
    read_from_cache: bool = True,
    write_to_cache: bool = True,
) -> list[Observation]:
    """
    Fetch elevation data from multiple providers with caching support.
    
    This function queries multiple elevation data providers in parallel and returns
    observations from each provider. Providers are automatically selected based on
    coordinate location (US vs international) unless explicitly specified.
    
    Args:
        latitude: Latitude in decimal degrees. Must be between -90 and 90.
        longitude: Longitude in decimal degrees. Must be between -180 and 180.
        providers: Optional list of provider names to use. If None, providers
            are automatically selected based on coordinate classification.
            Valid providers: ["usgs", "google", "osm", "open_topo_data"].
        timeout_seconds: Request timeout in seconds for each provider. Must be
            positive and <= 300 seconds.
        read_from_cache: Whether to read results from cache if available.
        write_to_cache: Whether to write results to cache for future use.
    
    Returns:
        List of Observation objects, one per provider. Each observation contains
        the elevation value (if successful), provider metadata, error information
        (if failed), and caching details.
    
    Raises:
        ValueError: If coordinates are outside valid ranges or if invalid
            provider names are specified.
        TimeoutError: If all providers exceed the timeout limit.
        
    Example:
        >>> service = ElevationService.from_env()
        >>> observations = await service.fetch_elevation_data(
        ...     latitude=37.7749,
        ...     longitude=-122.4194,
        ...     timeout_seconds=30.0
        ... )
        >>> successful_obs = [obs for obs in observations if obs.value_status == "ok"]
        >>> if successful_obs:
        ...     elevation = successful_obs[0].value_numeric
        ...     print(f"Elevation: {elevation}m")
    
    Note:
        This function implements smart provider routing:
        - US coordinates: Prefers USGS for high accuracy
        - International: Uses Open Topo Data and Google for global coverage
        - Ocean areas: Automatically handles providers that support marine locations
    """
    pass

# ❌ Bad: Minimal or missing docstring
async def fetch_elevation_data(latitude, longitude, providers=None):
    """Get elevation data."""
    pass
```

### README and Documentation Structure

```markdown
# Project Documentation Structure

docs/
├── README.md                 # Overview and quick start
├── CODING_STANDARDS.md      # This document
├── API_REFERENCE.md         # Complete API documentation
├── CONTRIBUTING.md          # Contribution guidelines
├── elevation/
│   ├── overview.md          # Elevation service overview
│   ├── providers.md         # Provider-specific documentation
│   ├── api_keys.md         # API key setup and configuration
│   └── examples.md         # Usage examples and tutorials
└── development/
    ├── setup.md            # Development environment setup
    ├── testing.md          # Testing guidelines
    └── deployment.md       # Deployment procedures
```

## Git and Version Control

### Commit Message Standards

Use conventional commits format with detailed descriptions:

```bash
# ✅ Good: Detailed conventional commit
git commit -m "feat(elevation): add multi-provider elevation service

Implements comprehensive elevation data fetching system with support for:
- USGS EPQS for high-accuracy US data
- Google Elevation API for global coverage  
- Open Topo Data for free global SRTM/ASTER data
- OSM Elevation for community-driven data

Features:
- Smart provider routing based on coordinate classification
- Comprehensive caching with coordinate canonicalization
- Async/await support for concurrent provider queries
- Rich error handling with fallback strategies
- Complete type safety with mypy compliance

Breaking Changes:
- None (new feature addition)

Closes #24"

# ❌ Bad: Vague commit message
git commit -m "add elevation stuff"
```

### Branch Naming

```bash
# ✅ Good: Descriptive branch names
git checkout -b 24-define-an-output-schema
git checkout -b feat/elevation-service-implementation
git checkout -b fix/coordinate-validation-edge-cases
git checkout -b docs/api-reference-update

# ❌ Bad: Non-descriptive names
git checkout -b my-changes
git checkout -b fix
git checkout -b temp
```

### Pull Request Standards

```markdown
## Pull Request Template

### Summary
Brief description of what this PR accomplishes.

### Changes Made
- **Feature**: Detailed list of new features
- **Bug Fixes**: List of bugs fixed with issue references
- **Documentation**: Documentation updates
- **Tests**: New or updated tests

### Testing
- [ ] All tests pass (`make check-ci`)
- [ ] New functionality has test coverage
- [ ] Manual testing performed
- [ ] Performance impact assessed

### Breaking Changes
List any breaking changes and migration steps.

### Dependencies
List any new dependencies added or updated.

### Checklist
- [ ] Code follows established patterns
- [ ] Documentation updated
- [ ] Type annotations complete
- [ ] Error handling implemented
- [ ] Logging added where appropriate
```

## Build System (Makefile)

### Makefile Standards

```makefile
# ✅ Good: Comprehensive Makefile with clear targets
.PHONY: help install install-dev test test-cov lint format type-check check-ci clean build docs
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(GREEN)Installing production dependencies...$(RESET)"
	uv sync --no-dev

install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(RESET)"
	uv sync

test: ## Run tests
	@echo "$(GREEN)Running tests...$(RESET)"
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	uv run pytest tests/ -v --cov=biosample_enricher --cov-report=html --cov-report=xml

lint: ## Run linting
	@echo "$(GREEN)Running linting...$(RESET)"
	uv run ruff check biosample_enricher/ tests/

format: ## Format code
	@echo "$(GREEN)Formatting code...$(RESET)"
	uv run ruff format biosample_enricher/ tests/

format-check: ## Check code formatting
	@echo "$(GREEN)Checking code formatting...$(RESET)"
	uv run ruff format --check biosample_enricher/ tests/

type-check: ## Run type checking
	@echo "$(GREEN)Running type checking...$(RESET)"
	uv run mypy biosample_enricher/

dep-check: ## Check dependencies
	@echo "$(GREEN)Checking dependencies...$(RESET)"
	uv run deptry .

check-ci: lint format-check type-check dep-check test ## Run all CI checks
	@echo "$(GREEN)All CI checks completed!$(RESET)"

clean: ## Clean build artifacts
	@echo "$(RED)Cleaning build artifacts...$(RESET)"
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Demonstration targets with dependencies
data/outputs/elevation/mount_rushmore.json: install-dev
	@echo "$(GREEN)Testing elevation lookup for Mount Rushmore...$(RESET)"
	uv run elevation-lookup lookup --lat 43.8791 --lon -103.4591 \
		--subject-id "mount-rushmore-demo" \
		--output $@

elevation-demo: data/outputs/elevation/mount_rushmore.json ## Run elevation demonstration
	@echo "$(GREEN)Elevation demonstration completed$(RESET)"

# Target patterns with error handling
build: clean install ## Build distribution packages
	@echo "$(GREEN)Building distribution packages...$(RESET)"
	uv build || (echo "$(RED)Build failed$(RESET)" && exit 1)

docs: install-dev ## Generate documentation
	@echo "$(GREEN)Generating documentation...$(RESET)"
	@mkdir -p docs/generated
	uv run python -m pydoc -w biosample_enricher
```

### Build Target Best Practices

```makefile
# ✅ Good: Proper dependency management and error handling
check-env: ## Validate environment setup
	@echo "$(GREEN)Checking environment setup...$(RESET)"
	@command -v uv >/dev/null 2>&1 || (echo "$(RED)uv not installed$(RESET)" && exit 1)
	@test -f .env || (echo "$(YELLOW)Warning: .env file not found$(RESET)")
	@echo "Environment check passed"

install-dev: check-env ## Install with environment validation
	@echo "$(GREEN)Installing development dependencies...$(RESET)"
	uv sync

test-integration: install-dev ## Run integration tests with proper setup
	@echo "$(GREEN)Running integration tests...$(RESET)"
	@test -n "$$GOOGLE_MAIN_API_KEY" || echo "$(YELLOW)Warning: Google API key not set$(RESET)"
	uv run pytest tests/ -v -m integration

# ❌ Bad: No error handling or dependencies
test:
	pytest tests/

install:
	uv sync
```

## Project Configuration (pyproject.toml)

### Comprehensive Configuration

```toml
# ✅ Good: Complete project configuration
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "biosample-enricher"
version = "0.1.0"
description = "Comprehensive biosample metadata enrichment with elevation, geolocation, and taxonomic data"
readme = "README.md"
license = {file = "LICENSE"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
maintainers = [
    {name = "Maintainer Name", email = "maintainer@example.com"}
]
keywords = [
    "biosample",
    "enrichment", 
    "elevation",
    "geolocation",
    "metadata",
    "scientific-data"
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Typing :: Typed"
]
requires-python = ">=3.11"
dependencies = [
    # Core dependencies with version constraints
    "click>=8.1.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0,<3.0.0",
    "requests>=2.31.0",
    "requests-cache>=1.0.0",
    "rich>=13.0.0",
    
    # Schema analysis dependencies
    "genson>=1.2.2",
    "pymongo>=4.5.0",
    "pandas>=2.0.0",
    
    # Environment and configuration
    "python-dotenv>=1.1.1",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    
    # Code quality
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    "deptry>=0.12.0",
    
    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.2.0",
    "mkdocstrings[python]>=0.23.0",
]

[project.scripts]
biosample-enricher = "biosample_enricher.cli:main"
elevation-lookup = "biosample_enricher.cli_elevation:elevation_cli"
elevation-demos = "biosample_enricher.elevation_demos:cli"
biosample-elevation = "biosample_enricher.cli_biosample_elevation:cli"
http-cache-manager = "biosample_enricher.cache_management:cli"

[project.urls]
Homepage = "https://github.com/your-org/biosample-enricher"
Documentation = "https://your-org.github.io/biosample-enricher"
Repository = "https://github.com/your-org/biosample-enricher"
Issues = "https://github.com/your-org/biosample-enricher/issues"
Changelog = "https://github.com/your-org/biosample-enricher/blob/main/CHANGELOG.md"

# Tool configurations
[tool.ruff]
target-version = "py311"
line-length = 88
extend-exclude = [
    "migrations",
    "venv",
    ".venv",
    "__pycache__",
    "build",
    "dist"
]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "RUF",    # Ruff-specific rules
]
ignore = [
    "E501",   # Line too long (handled by formatter)
    "B008",   # Do not perform function calls in argument defaults
    "C901",   # Too complex (let complexity emerge naturally)
    "W505",   # Doc line too long
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "ARG001",  # Unused function argument (common in test fixtures)
    "S101",    # Use of assert (expected in tests)
]

[tool.ruff.lint.isort]
known-first-party = ["biosample_enricher"]
force-single-line = false
lines-after-imports = 2

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
implicit_reexport = false
strict_equality = true
extra_checks = true

[[tool.mypy.overrides]]
module = [
    "pymongo.*",
    "requests_cache.*",
    "genson.*",
]
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--tb=short",
    "--durations=10",
]
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (may require API keys)",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "unit: marks tests as unit tests",
]
asyncio_mode = "strict"

[tool.coverage.run]
source = ["biosample_enricher"]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
    "*/venv/*",
    "*/.venv/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.deptry]
ignore = ["DEP002"]  # Allow unused dependencies (for optional features)
exclude = [
    ".venv",
    "venv", 
    "tests",
    "migrations",
]

[tool.hatch.build.targets.wheel]
packages = ["biosample_enricher"]
```

## GitHub Actions and CI/CD

### Comprehensive CI Pipeline

```yaml
# .github/workflows/ci.yml - ✅ Good: Complete CI pipeline
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    # Run tests daily at 6 AM UTC to catch dependency issues
    - cron: '0 6 * * *'

env:
  PYTHON_VERSION: "3.11"

jobs:
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"
          
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run linting
        run: uv run ruff check biosample_enricher/ tests/
        
      - name: Check formatting
        run: uv run ruff format --check biosample_enricher/ tests/
        
      - name: Run type checking
        run: uv run mypy biosample_enricher/
        
      - name: Check dependencies
        run: uv run deptry .

  test:
    name: Tests
    runs-on: ${{ matrix.os }}
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.11", "3.12"]
        
    services:
      mongodb:
        image: mongo:7.0
        ports:
          - 27017:27017
        options: >-
          --health-cmd mongosh
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"
          
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run unit tests
        run: uv run pytest tests/ -v -m "not integration" --cov=biosample_enricher
        env:
          MONGO_URI: mongodb://localhost:27017
          
      - name: Run integration tests
        run: uv run pytest tests/ -v -m integration --cov=biosample_enricher --cov-append
        env:
          MONGO_URI: mongodb://localhost:27017
          GOOGLE_MAIN_API_KEY: ${{ secrets.GOOGLE_MAIN_API_KEY }}
        continue-on-error: true  # Don't fail CI if external APIs are down
        
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: false

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run safety check
        run: uv run safety check
        continue-on-error: true
        
      - name: Run bandit security scan
        run: uv run bandit -r biosample_enricher/
        continue-on-error: true

  build:
    name: Build Distribution
    runs-on: ubuntu-latest
    needs: [quality, test]
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
        
      - name: Build package
        run: uv build
        
      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  docs:
    name: Documentation
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        
      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}
        
      - name: Install dependencies
        run: uv sync
        
      - name: Build documentation
        run: uv run mkdocs build --strict
        
      - name: Upload documentation
        uses: actions/upload-artifact@v4
        with:
          name: docs
          path: site/

  # Release job (only on tags)
  release:
    name: Release
    runs-on: ubuntu-latest
    needs: [quality, test, build]
    if: startsWith(github.ref, 'refs/tags/')
    timeout-minutes: 15
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
          
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
          
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

### Workflow Best Practices

```yaml
# ✅ Good: Security and efficiency practices
name: Secure CI Pipeline

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write

env:
  PYTHONHASHSEED: 0  # Reproducible builds
  FORCE_COLOR: 1     # Colored output

jobs:
  changes:
    name: Detect Changes
    runs-on: ubuntu-latest
    outputs:
      python: ${{ steps.changes.outputs.python }}
      docs: ${{ steps.changes.outputs.docs }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            python:
              - '**/*.py'
              - 'pyproject.toml'
              - 'uv.lock'
            docs:
              - 'docs/**'
              - 'README.md'

  test:
    name: Tests
    needs: changes
    if: needs.changes.outputs.python == 'true'
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout with token
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/uv
          key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-
```

## Dependencies and Environment

### Dependency Management

```toml
# pyproject.toml - ✅ Good: Precise dependency specification
[project]
dependencies = [
    # Core dependencies with compatibility constraints
    "pydantic>=2.0.0,<3.0.0",      # Major version constraint
    "httpx>=0.25.0,<1.0.0",        # Proven version range
    "click>=8.1.0",                # Minimum version (stable API)
    "rich>=13.0.0",                # Feature requirement
    
    # Pin transitive dependencies that break compatibility
    "anyio>=3.7.0,<5.0.0",         # httpx compatibility
    
    # Scientific dependencies with proven versions
    "pandas>=2.0.0,<3.0.0",
    "numpy>=1.24.0",               # pandas compatibility
]

[project.optional-dependencies]
dev = [
    # Testing with version constraints
    "pytest>=7.4.0,<9.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    
    # Code quality - allow latest
    "mypy>=1.5.0",
    "ruff>=0.1.0",
    
    # Documentation
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.2.0",
]

# Production deployment
production = [
    "gunicorn>=21.0.0",
    "uvicorn[standard]>=0.23.0",
]
```

### Environment Configuration

```python
# biosample_enricher/config.py - ✅ Good: Centralized configuration
import os
from pathlib import Path
from typing import Any

from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Core application settings
    app_name: str = "biosample-enricher"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database settings
    mongo_uri: str = Field(default="mongodb://localhost:27017", env="MONGO_URI")
    mongo_database: str = Field(default="biosample_enricher", env="MONGO_DATABASE")
    
    # API keys (optional)
    google_api_key: str | None = Field(default=None, env="GOOGLE_MAIN_API_KEY")
    
    # Caching settings
    cache_backend: str = Field(default="mongodb", env="CACHE_BACKEND")
    cache_ttl_seconds: int = Field(default=86400, env="CACHE_TTL_SECONDS")
    
    # Request settings
    default_timeout_seconds: float = Field(default=30.0, env="DEFAULT_TIMEOUT_SECONDS")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="structured", env="LOG_FORMAT")
    
    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @validator('cache_backend')
    def validate_cache_backend(cls, v: str) -> str:
        """Validate cache backend."""
        valid_backends = {"mongodb", "sqlite", "memory"}
        if v.lower() not in valid_backends:
            raise ValueError(f"Invalid cache backend: {v}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

## Security Standards

### API Key and Secret Management

```python
# ✅ Good: Secure credential handling
import os
from typing import Optional
from functools import lru_cache

class CredentialManager:
    """Secure credential management with fallback strategies."""
    
    @staticmethod
    @lru_cache(maxsize=None)
    def get_api_key(service: str) -> Optional[str]:
        """
        Get API key for service with secure fallback.
        
        Priority order:
        1. Environment variable (production)
        2. .env file (development)
        3. Keyring (local development)
        4. None (graceful degradation)
        """
        # Environment variable (production deployment)
        env_var = f"{service.upper()}_API_KEY"
        api_key = os.getenv(env_var)
        
        if api_key:
            # Validate key format without logging the actual key
            if len(api_key) >= 10:  # Minimum reasonable length
                logger.debug(f"Found {service} API key from environment")
                return api_key
            else:
                logger.warning(f"Invalid {service} API key format in {env_var}")
        
        # Fallback: try alternative environment variable names
        alt_names = {
            "google": ["GOOGLE_MAIN_API_KEY", "GOOGLE_MAPS_API_KEY"],
            "openai": ["OPENAI_API_KEY", "OPENAI_TOKEN"],
        }
        
        for alt_name in alt_names.get(service, []):
            api_key = os.getenv(alt_name)
            if api_key and len(api_key) >= 10:
                logger.debug(f"Found {service} API key from {alt_name}")
                return api_key
        
        logger.info(f"No {service} API key found - service will be disabled")
        return None
    
    @staticmethod
    def validate_api_key_format(service: str, api_key: str) -> bool:
        """Validate API key format without external calls."""
        validators = {
            "google": lambda k: k.startswith("AIza") and len(k) == 39,
            "openai": lambda k: k.startswith("sk-") and len(k) >= 40,
        }
        
        validator = validators.get(service)
        if validator:
            return validator(api_key)
        
        # Generic validation
        return len(api_key) >= 10 and not api_key.isspace()

# ❌ Bad: Insecure credential handling
def get_google_key():
    return "AIzaSyDobykt5XGvScGaLXojw-OUexaK2NBfO98"  # Hardcoded key

def log_api_request(api_key, url):
    logger.info(f"Making request to {url} with key {api_key}")  # Logs secret
```

### Input Validation and Sanitization

```python
# ✅ Good: Comprehensive input validation
from pydantic import BaseModel, Field, validator
import re
from typing import Any

class CoordinateInput(BaseModel):
    """Secure coordinate input validation."""
    
    latitude: float = Field(
        ge=-90.0, 
        le=90.0, 
        description="Latitude in decimal degrees"
    )
    longitude: float = Field(
        ge=-180.0, 
        le=180.0, 
        description="Longitude in decimal degrees"
    )
    
    @validator('latitude', 'longitude', pre=True)
    def validate_numeric_input(cls, v: Any) -> float:
        """Validate and sanitize numeric coordinates."""
        if isinstance(v, str):
            # Remove whitespace
            v = v.strip()
            
            # Check for injection attempts
            if re.search(r'[<>"\';\\]', v):
                raise ValueError("Invalid characters in coordinate")
            
            # Convert to float
            try:
                v = float(v)
            except ValueError:
                raise ValueError(f"Cannot convert '{v}' to float")
        
        if not isinstance(v, (int, float)):
            raise ValueError("Coordinate must be numeric")
        
        # Check for NaN and infinity
        if not (-180 <= v <= 180):  # Covers both lat and lon ranges
            raise ValueError("Coordinate out of valid range")
        
        return float(v)

class SecureFileInput(BaseModel):
    """Secure file input validation."""
    
    filename: str = Field(max_length=255)
    content_type: str = Field(regex=r'^[a-zA-Z0-9][a-zA-Z0-9\-\/]+$')
    
    @validator('filename')
    def validate_filename(cls, v: str) -> str:
        """Validate filename for security."""
        # Remove path traversal attempts
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid filename: path traversal detected")
        
        # Check for dangerous extensions
        dangerous_exts = {'.exe', '.bat', '.sh', '.php', '.jsp'}
        if any(v.lower().endswith(ext) for ext in dangerous_exts):
            raise ValueError("Dangerous file extension not allowed")
        
        # Sanitize filename
        v = re.sub(r'[^\w\-_\.]', '_', v)
        
        return v
```

## Performance Guidelines

### Async/Await Best Practices

```python
# ✅ Good: Efficient async patterns
import asyncio
import httpx
from typing import List
from contextlib import asynccontextmanager

class ElevationService:
    """High-performance elevation service with connection pooling."""
    
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
    
    @asynccontextmanager
    async def _get_client(self):
        """Context manager for HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                ),
                http2=True,  # Enable HTTP/2 for better performance
            )
        
        try:
            yield self._client
        finally:
            # Client cleanup handled in __aexit__
            pass
    
    async def fetch_elevations_batch(
        self, 
        coordinates: List[tuple[float, float]],
    ) -> List[ElevationResult]:
        """Fetch elevations for multiple coordinates efficiently."""
        async with self._get_client() as client:
            # Process in batches to avoid overwhelming servers
            batch_size = 50
            results = []
            
            for i in range(0, len(coordinates), batch_size):
                batch = coordinates[i:i + batch_size]
                batch_tasks = [
                    self._fetch_single_with_semaphore(client, lat, lon)
                    for lat, lon in batch
                ]
                
                # Wait for batch completion before starting next batch
                batch_results = await asyncio.gather(
                    *batch_tasks, 
                    return_exceptions=True
                )
                results.extend(batch_results)
                
                # Brief delay between batches to be respectful to APIs
                if i + batch_size < len(coordinates):
                    await asyncio.sleep(0.1)
            
            return results
    
    async def _fetch_single_with_semaphore(
        self, 
        client: httpx.AsyncClient, 
        lat: float, 
        lon: float
    ) -> ElevationResult:
        """Fetch single elevation with rate limiting."""
        async with self._semaphore:
            return await self._fetch_single(client, lat, lon)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

# ❌ Bad: Inefficient async patterns
class SlowElevationService:
    async def fetch_elevations(self, coordinates):
        results = []
        for lat, lon in coordinates:
            # Creates new client for each request - very inefficient
            async with httpx.AsyncClient() as client:
                result = await client.get(f"https://api.example.com?lat={lat}&lon={lon}")
                results.append(result.json())
        return results
```

### Caching and Memory Management

```python
# ✅ Good: Efficient caching with memory management
from functools import lru_cache
from typing import Dict, Optional
import weakref
import asyncio

class SmartCache:
    """Memory-efficient cache with automatic cleanup."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def __aenter__(self):
        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache with TTL check."""
        current_time = time.time()
        
        if key in self._cache:
            value, timestamp = self._cache[key]
            
            # Check TTL
            if current_time - timestamp < self.ttl_seconds:
                self._access_times[key] = current_time
                return value
            else:
                # Expired - remove
                del self._cache[key]
                self._access_times.pop(key, None)
        
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set item in cache with size management."""
        current_time = time.time()
        
        # Evict if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            await self._evict_lru()
        
        self._cache[key] = (value, current_time)
        self._access_times[key] = current_time
    
    async def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=self._access_times.get)
        del self._cache[lru_key]
        del self._access_times[lru_key]
    
    async def _periodic_cleanup(self) -> None:
        """Background task to clean expired items."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                current_time = time.time()
                
                expired_keys = [
                    key for key, (_, timestamp) in self._cache.items()
                    if current_time - timestamp >= self.ttl_seconds
                ]
                
                for key in expired_keys:
                    del self._cache[key]
                    self._access_times.pop(key, None)
                    
            except asyncio.CancelledError:
                break

# Coordinate canonicalization with efficient caching
@lru_cache(maxsize=10000)
def canonicalize_coordinate_pair(lat: float, lon: float) -> tuple[float, float]:
    """Cache coordinate canonicalization for efficiency."""
    # Round to 4 decimal places (~10m precision)
    return (round(lat, 4), round(lon, 4))
```

## Code Review Guidelines

### Review Checklist

**Functionality**:
- [ ] Code solves the stated problem completely
- [ ] Edge cases are handled appropriately
- [ ] Error conditions are handled gracefully
- [ ] No obvious bugs or logical errors

**Design**:
- [ ] Code follows single responsibility principle
- [ ] Abstractions are appropriate and not over-engineered
- [ ] Interfaces are clean and well-defined
- [ ] No code duplication (DRY principle)

**Code Quality**:
- [ ] Code is readable and self-documenting
- [ ] Variable and function names are clear and descriptive
- [ ] Comments explain "why", not "what"
- [ ] Complex logic is broken down into smaller functions

**Testing**:
- [ ] New functionality has comprehensive test coverage
- [ ] Tests cover both success and failure cases
- [ ] Tests are independent and can run in any order
- [ ] Mock usage is appropriate and not excessive

**Security**:
- [ ] Input validation is comprehensive
- [ ] No hardcoded secrets or credentials
- [ ] External data is sanitized appropriately
- [ ] Authentication/authorization is handled correctly

**Performance**:
- [ ] No obvious performance bottlenecks
- [ ] Database queries are efficient
- [ ] Async/await is used appropriately
- [ ] Memory usage is reasonable

**Standards Compliance**:
- [ ] All CI checks pass (`make check-ci`)
- [ ] Code follows established patterns
- [ ] Documentation is updated
- [ ] Breaking changes are documented

### Review Process

1. **Automated Checks**: Ensure all CI checks pass before human review
2. **Self-Review**: Author reviews their own code first
3. **Peer Review**: At least one other developer reviews
4. **Subject Matter Expert**: Domain expert reviews if applicable
5. **Security Review**: Security-focused review for sensitive changes

### Review Comments

```markdown
# ✅ Good: Constructive review comments

## Suggestion: Consider caching optimization
The coordinate lookup in `get_elevation()` could benefit from caching since it's called frequently. Consider adding an LRU cache or using the existing cache infrastructure.

```python
@lru_cache(maxsize=1000)
def lookup_coordinate_metadata(lat: float, lon: float) -> CoordinateInfo:
    # implementation
```

## Issue: Missing error handling
Lines 45-50 don't handle the case where the API returns a 429 rate limit error. This could cause the entire batch to fail.

**Suggested fix**: Add retry logic with exponential backoff for rate limits.

## Praise: Excellent type annotations
The type annotations in this module are comprehensive and make the code very clear. The use of protocols for the provider interface is particularly nice.

# ❌ Bad: Non-constructive review comments

- "This is wrong"
- "Rewrite this"
- "I don't like this approach"
- "Use pattern X instead" (without explanation)
```

## Enforcement and Tooling

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
```

### IDE Configuration

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "none",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": true,
            "source.organizeImports.ruff": true
        }
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "mypy.runUsingActiveInterpreter": true
}
```

## Conclusion

These coding standards ensure:

1. **Consistency**: All code follows the same patterns and conventions
2. **Quality**: High code quality through comprehensive tooling and review
3. **Security**: Secure handling of credentials and user input
4. **Performance**: Efficient async patterns and resource management
5. **Maintainability**: Clear, well-documented, and testable code
6. **Reliability**: Comprehensive testing and error handling

**Remember**: These standards are enforced automatically through CI/CD - all checks must pass before code can be merged. No exceptions, no workarounds, no shortcuts.

The goal is to write code that is not just functional, but exemplary - code that serves as a reference for how Python projects should be built and maintained.