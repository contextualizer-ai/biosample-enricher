# Release Process

This document describes the complete release process for biosample-enricher, including TestPyPI validation and production PyPI publication.

## Overview

We use a two-stage release process:
1. **TestPyPI** - Safe testing environment for release candidates
2. **Production PyPI** - Final publication for stable releases

Both use **Trusted Publishing** (OIDC) - no API tokens needed!

## Prerequisites

### One-Time Setup

1. **TestPyPI Trusted Publisher** (Already configured ✅)
   - Project: `biosample-enricher`
   - Repository: `contextualizer-ai/biosample-enricher`
   - Workflow: `test-release.yml`

2. **Production PyPI Trusted Publisher** (Required before first release)
   - Go to https://pypi.org
   - Add pending publisher:
     - Project: `biosample-enricher`
     - Repository: `contextualizer-ai/biosample-enricher`
     - Workflow: `release.yml`
     - Environment: (none)

## Release Workflow

### Step 1: Create Release Candidate

```bash
# Ensure you're on main with latest changes
git checkout main
git pull origin main

# Create RC tag (increment RC number for each attempt)
git tag -a v0.1.0-rc1 -m "Release candidate 1 for v0.1.0"
git push origin v0.1.0-rc1
```

This triggers `.github/workflows/test-release.yml`:
- ✅ Runs quality checks (ruff, mypy)
- ✅ Runs fast tests
- ✅ Builds package
- ✅ Publishes to TestPyPI

### Step 2: Validate TestPyPI Package

Wait ~5 minutes for TestPyPI to process, then:

```bash
# Create clean test environment
python -m venv test-env
source test-env/bin/activate  # Windows: test-env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple \
    biosample-enricher

# Test basic functionality
python -c "
from biosample_enricher import (
    ElevationService,
    SoilService,
    WeatherService,
    MarineService,
    LandService,
    ReverseGeocodingService,
    ForwardGeocodingService,
    OSMFeaturesService,
)
print('✅ All services imported successfully')
"

# Test elevation service
python -c "
from biosample_enricher import ElevationService, ElevationRequest

service = ElevationService()
request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
observations = service.get_elevation(request)
print(f'✅ Elevation service works: {len(observations)} observations')
"

# Test package metadata
pip show biosample-enricher

# Cleanup
deactivate
rm -rf test-env
```

### Step 3: Validation Checklist

- [ ] Package installs from TestPyPI without errors
- [ ] All 8 services can be imported
- [ ] Basic service functionality works (e.g., elevation lookup)
- [ ] Package metadata looks correct (version, description, keywords, classifiers)
- [ ] README displays correctly on TestPyPI page
- [ ] Dependencies install correctly from main PyPI

### Step 4: Production Release

If validation passes, create production release:

```bash
# Option A: Via GitHub CLI
gh release create v0.1.0 \
    --title "v0.1.0: Initial Release" \
    --generate-notes

# Option B: Via GitHub Web UI
# 1. Go to https://github.com/contextualizer-ai/biosample-enricher/releases/new
# 2. Choose tag: Create new tag "v0.1.0" on publish
# 3. Title: "v0.1.0: Initial Release"
# 4. Click "Generate release notes" for auto-populated changelog
# 5. Uncheck "Set as a pre-release"
# 6. Click "Publish release"
```

This triggers `.github/workflows/release.yml`:
- ✅ Runs quality checks
- ✅ Runs fast tests
- ✅ Builds package
- ✅ Publishes to production PyPI

### Step 5: Verify Production Release

```bash
# Wait ~5 minutes, then install from PyPI
pip install biosample-enricher

# Verify installation
python -c "
from biosample_enricher import ElevationService
print('✅ Production package works!')
"

# Check PyPI page
open https://pypi.org/project/biosample-enricher/
```

## Troubleshooting

### TestPyPI Publication Fails

1. Check GitHub Actions logs for error details
2. Common issues:
   - Tests failing: Fix tests and create new RC tag
   - Build errors: Check pyproject.toml syntax
   - Version conflict: TestPyPI doesn't allow re-uploading same version

### Production PyPI Publication Fails

1. **Trusted Publisher Not Configured**
   - Go to https://pypi.org and add pending publisher (see Prerequisites)

2. **Tests Failing**
   - Should have been caught in TestPyPI validation
   - Delete the GitHub release, fix issues, create new RC

3. **Version Already Exists**
   - PyPI versions are immutable
   - Increment version number and try again

## Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** (v1.0.0 → v2.0.0): Breaking changes
- **MINOR** (v0.1.0 → v0.2.0): New features (backward compatible)
- **PATCH** (v0.1.0 → v0.1.1): Bug fixes (backward compatible)

Release candidates: `v0.1.0-rc1`, `v0.1.0-rc2`, etc.

## Release Checklist

Before creating release candidate:

- [ ] All tests passing in CI
- [ ] README.md is up to date
- [ ] CONTRIBUTING.md has latest guidelines
- [ ] No unmerged critical PRs
- [ ] Version number follows semantic versioning
- [ ] Decide on version number (major.minor.patch)

After successful production release:

- [ ] Verify package on PyPI
- [ ] Update GitHub release notes if needed
- [ ] Announce release (Twitter, Discord, mailing list, etc.)
- [ ] Close milestone if using GitHub milestones

## Emergency: Yanking a Release

If a critical bug is found after release:

```bash
# Yank the broken version (makes it unavailable for new installs)
pip install twine
python -m twine yank biosample-enricher <version> --repository pypi
# Or use the PyPI web UI to yank the version:
# https://pypi.org/project/biosample-enricher/<version>/

# Immediately release a patch version
git tag v0.1.1
# Follow normal release process
```

**Note**: Yanked versions remain available for existing users but won't be installed for new users.
