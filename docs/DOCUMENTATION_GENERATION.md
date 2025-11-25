# Documentation Generation Guide

This document describes the automated documentation generation tools available in biosample-enricher.

## Overview

The biosample-enricher project uses a YAML-based metadata system to maintain comprehensive documentation about all data providers. This metadata is used to generate:

1. **Python Docstrings** - Auto-generated class docstrings visible in IDEs and `help()`
2. **API Index** - Alphabetical index of all public functions and methods
3. **Provider Documentation** - Comprehensive markdown documentation with comparison tables

## Documentation Tools

### 1. Provider Docstring Generator

**Purpose**: Updates Python class docstrings from YAML metadata

**Source**: `scripts/generate_provider_docstrings.py`

**Usage**:
```bash
# Preview changes without modifying files
uv run generate-provider-docstrings --dry-run

# Update specific provider
uv run generate-provider-docstrings --provider weather.meteostat

# Update all providers
uv run generate-provider-docstrings
```

**Output**: Updates docstrings in Python files under `biosample_enricher/`

**When to Run**:
- After modifying `config/provider_metadata.yaml`
- When adding a new provider
- To ensure IDE documentation is up-to-date

### 2. API Index Generator

**Purpose**: Creates alphabetical index of all public functions and methods

**Source**: `scripts/generate_api_index.py`

**Usage**:
```bash
# Generate index (default output: docs/API_INDEX.md)
uv run generate-api-index

# Custom output location
uv run generate-api-index --output path/to/output.md
```

**Output**: `docs/API_INDEX.md` - Alphabetical listing of 398 functions and methods

**When to Run**:
- After adding new public functions or methods
- Before releases to update API documentation
- When restructuring code

### 3. Provider Documentation Generator

**Purpose**: Creates comprehensive markdown documentation with comparison tables

**Source**: `scripts/generate_provider_docs.py`

**Usage**:
```bash
# Generate documentation (default output: docs/PROVIDERS.md)
uv run generate-provider-docs

# Custom output location
uv run generate-provider-docs --output path/to/output.md
```

**Output**: `docs/PROVIDERS.md` - Provider profiles with:
- Overview comparison table
- Domain-specific comparison tables
- Detailed provider profiles with strengths/weaknesses
- Use case recommendations
- NMDC integration details

**When to Run**:
- After modifying `config/provider_metadata.yaml`
- When adding a new provider
- Before releases to update user documentation

## Source of Truth: provider_metadata.yaml

All documentation is generated from `config/provider_metadata.yaml`, which contains:

### Systematic Comparison Criteria

Each provider entry includes:

1. **Technical Characteristics**
   - API type (REST, Python Library, etc.)
   - Endpoint URL
   - Authentication requirements
   - Coverage (global, regional, etc.)
   - Resolution (spatial/temporal)
   - Data freshness

2. **Reliability**
   - Stability level (HIGH, MODERATE, LOW)
   - Data quality (ground_truth, satellite, model, etc.)
   - Uptime history
   - Known issues

3. **Cost**
   - Pricing model (free, paid, freemium)
   - Free tier details
   - Quota limits

4. **Strengths** (bulleted list)
   - What this provider does well
   - Advantages over alternatives

5. **Weaknesses** (bulleted list)
   - Limitations
   - When not to use this provider

6. **Use Cases**
   - Best for: Ideal scenarios
   - Not suitable for: When to avoid
   - Complements: Providers that work well together

7. **NMDC Integration**
   - Schema slots mapped
   - Multi-provider role (primary, fallback, etc.)
   - Geographic preferences (excellent/poor regions)

## Workflow

### Adding a New Provider

1. **Update YAML metadata**: Add complete entry to `config/provider_metadata.yaml`
2. **Generate docstrings**: Run `uv run generate-provider-docstrings`
3. **Update documentation**: Run `uv run generate-provider-docs`
4. **Regenerate index**: Run `uv run generate-api-index` (if new public methods added)
5. **Commit all changes**: YAML, Python files, and generated docs

### Updating Provider Information

1. **Edit YAML**: Modify `config/provider_metadata.yaml`
2. **Regenerate docstrings**: Run `uv run generate-provider-docstrings`
3. **Update documentation**: Run `uv run generate-provider-docs`
4. **Commit changes**

### Before Release

Run all three generators to ensure documentation is current:

```bash
make update-docs  # If you add this target to Makefile
# Or manually:
uv run generate-provider-docstrings
uv run generate-api-index
uv run generate-provider-docs
```

## Benefits

### 1. Single Source of Truth
- All provider information in one YAML file
- No duplicate documentation
- Easy to maintain consistency

### 2. IDE Integration
- Class docstrings visible in autocomplete
- `help()` function shows comprehensive info
- Developer-friendly

### 3. User Documentation
- Comparison tables for quick reference
- Detailed profiles for deep dives
- Use case recommendations

### 4. Automated Updates
- Scripts ensure documentation stays current
- No manual markdown editing required
- Reduced maintenance burden

## File Structure

```
biosample-enricher/
├── config/
│   └── provider_metadata.yaml          # Source of truth
├── scripts/
│   ├── generate_provider_docstrings.py # Python docstring generator
│   ├── generate_api_index.py           # API index generator
│   └── generate_provider_docs.py       # Markdown docs generator
├── docs/
│   ├── API_INDEX.md                    # Generated: Function/method index
│   ├── PROVIDERS.md                    # Generated: Provider docs
│   └── DOCUMENTATION_GENERATION.md     # This file
└── biosample_enricher/
    └── */providers/*.py                # Updated: Class docstrings
```

## Maintenance Notes

- **Never edit generated files directly** - They will be overwritten
- **Always update YAML first**, then regenerate
- **Test docstrings** with `help(ProviderClass)` after generation
- **Review diffs** before committing to catch errors
- **Keep YAML consistent** - Follow existing patterns

## Example Provider Entry

```yaml
weather.meteostat:
  name: "Meteostat"
  class: "MeteostatProvider"
  module: "biosample_enricher.weather.providers.meteostat"

  technical:
    api_type: "Python_Library_CDN"
    api_endpoint: "https://bulk.meteostat.net/v2/"
    authentication: "none"
    coverage: "Global (120,000+ stations)"
    resolution: "Station-based (point measurements)"
    temporal_coverage: "1973-present (daily), 1991-2020 (normals)"
    data_freshness: "7-day lag"

  reliability:
    stability: "high"
    data_quality: "ground_truth"
    uptime_history: "Excellent (stable library)"
    known_issues:
      - "Climate normals only available for WMO standard periods"
      - "Station coverage sparse in remote regions"

  cost:
    pricing_model: "free"
    free_tier: "Unlimited"

  strengths:
    - "30-year WMO standard period (1991-2020)"
    - "Station-based ground truth measurements"
    - "No API key required"

  weaknesses:
    - "Sparse coverage in remote regions"
    - "Distance uncertainty (may use station 50-100km away)"

  use_cases:
    best_for:
      - "Urban/suburban locations with dense station coverage"
      - "When WMO-standard 30-year normals required"
    not_suitable_for:
      - "Remote desert/mountain/ocean locations"
      - "Custom time periods (not WMO standard)"
    complements:
      - "NASA POWER (for remote area coverage)"

  nmdc_integration:
    schema_slots: ["annual_precpt", "annual_temp", "temp", "air_temp"]
    multi_provider_role: "primary_for_stations"
    geographic_preferences:
      excellent: ["urban", "suburban", "europe", "north_america"]
      poor: ["deserts", "mountains", "oceans", "remote_regions"]
```

## Future Enhancements

Potential improvements:

1. **HTML generation** - Convert markdown to styled HTML
2. **JSON schema validation** - Validate YAML structure
3. **Coverage reports** - Track documentation completeness
4. **Cross-references** - Link related providers automatically
5. **Version tracking** - Document when provider info last updated
6. **Performance benchmarks** - Add timing data to profiles

---

*This documentation system was created to ensure comprehensive, consistent, and maintainable provider documentation across the biosample-enricher project.*
