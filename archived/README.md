# Archived Code

This directory contains code that has been temporarily archived to simplify the project's focus on **NMDC submission-schema value retrieval**.

## Why Archived?

Following feedback from NMDC team members who found the documentation confusing ("what does it mean to get X for/from a biosample?"), we've archived code that:

1. **Shows future capabilities** not yet ready for users (MongoDB integration, schema alignment)
2. **Provides multiple ways** to accomplish the same task (violates "one way to do things" principle)
3. **Distracts from core use case** - getting submission values with `get_submission_values()`

This is **not deleted code** - it's fully version controlled and can be restored anytime.

## What's Archived

### `examples/` - Old Example Scripts (4,887 lines)

**Contents**: 11 demonstration scripts from before the archive

**MongoDB/Adapter Examples** (8 files, ~4,000 lines):
- `nmdc_adapter_demo.py` - MongoDB NMDC biosample adapter
- `gold_adapter_demo.py` - MongoDB GOLD biosample adapter
- `unified_adapter_demo.py` - Unified adapter combining NMDC/GOLD
- `mongodb_connection_demo.py` - MongoDB connection and querying
- `id_retrieval_demo.py` - ID retrieval from MongoDB
- `random_sampling_demo.py` - Random biosample sampling
- `pydantic_validation_demo.py` - Pydantic validation examples
- `synthetic_validation_demo.py` - Synthetic data validation

**Service-Level Examples** (3 files, ~640 lines):
- `climate_normals_multi_provider.py` - Multi-provider climate comparison
- `weather_demo.py` - Weather service demonstration
- `geocoding_comprehensive_demo.py` - Geocoding examples

**Tests** (5 files):
- `test_adapters.py` - MongoDB adapter tests
- `test_schema_tools.py` - Schema inference tests
- `test_biosample_elevation_mapper.py` - Legacy elevation mapper tests
- `test_demo_scripts.py` - Demo script tests
- `test_cli_main.py` - Main CLI tests (required MongoDB)

**Why Archived**:
- MongoDB examples don't work without MongoDB setup (confusing for users)
- Service examples show low-level APIs instead of `get_submission_values()`
- Created "multiple ways to do things" confusion
- Tests required optional dependencies (pymongo) that most users don't have

**Replaced With**:
- New simple examples in `examples/` showing ONLY `get_submission_values()`
- See: `examples/basic_climate.py`, `examples/error_handling.py`, etc.

## When to Restore

### MongoDB Integration (Issue #189)

When implementing the NMDC Submission Schema Transformer, restore:
- MongoDB adapter examples
- Related tests
- Documentation about reading biosamples from MongoDB

**Restoration**:
```bash
git mv archived/examples/nmdc_adapter_demo.py examples/
git mv archived/examples/mongodb_connection_demo.py examples/
git mv archived/examples/test_adapters.py tests/
# etc.
```

### Service-Level Documentation

If we decide advanced users need access to low-level service APIs (WeatherService, ElevationService, etc.), restore the service examples:

```bash
git mv archived/examples/climate_normals_multi_provider.py examples/
git mv archived/examples/weather_demo.py examples/
```

But ensure these are clearly marked "Advanced" and not the primary user path.

## Restoration Process

### Full Restoration of Examples

```bash
# Move everything back
git mv archived/examples/*.py examples/
git mv archived/examples/test_*.py tests/

# Update documentation config
# Remove "archived" from exclude_patterns in docs/source/conf.py

# Regenerate API index
uv run generate-api-index

# Commit
git add -A
git commit -m "Restore archived examples"
```

### Partial Restoration

```bash
# Restore only specific files
git mv archived/examples/nmdc_adapter_demo.py examples/
git mv archived/examples/test_adapters.py tests/

# Run tests to ensure nothing breaks
uv run pytest tests/test_adapters.py

# Commit
git add -A
git commit -m "Restore NMDC adapter example"
```

## Related Issues

- **Issue #204**: Shift focus from abstract "biosample enriching" to "suggesting for NMDC submissions"
- **Issue #203**: Give dev users the best possible documentation browsing/searching experience
- **Issue #189**: Implement NMDC Submission Schema Transformer (when ready, restore MongoDB examples)
- **Issue #199**: Design: Balance between general-purpose API and project-specific helpers

## Design Philosophy

The decision to archive was based on this principle:

> **There should be one—and preferably only one—obvious way to do it.**
>
> — The Zen of Python

For NMDC users:
- **One function**: `get_submission_values()`
- **One pattern**: Pass lat/lon/slots, get values back
- **One documentation path**: Read submission_values.rst, copy example, done

The archived code represented multiple approaches (services, adapters, CLIs) that made this unclear.

## Questions?

If you need to restore archived code or aren't sure why something was archived, check:
1. This README
2. Git history: `git log --follow archived/examples/<file>`
3. Related GitHub issues listed above
4. The commit message that moved code here

The archive was created on 2025-11-25 as part of simplifying the user experience for NMDC submission value retrieval.
