# Archive Plan: Focus on NMDC Submission Values

## Goal

Simplify the codebase and documentation by archiving future-development code that distracts from the core use case: **getting NMDC submission-schema values**.

## What Gets Archived

### Phase 1: MongoDB/Schema Alignment (Future Development)

**Files to move to `archived/mongodb/`:**
- `biosample_enricher/adapters.py` (535 lines) - MongoDB→NMDC/GOLD transformation
- `biosample_enricher/schema_inference.py` (36 lines) - Schema detection
- `biosample_enricher/schema_statistics.py` (101 lines) - Coverage stats
- `biosample_enricher/biosample_elevation_mapper.py` (152 lines) - Legacy elevation mapper
- `tests/test_adapters.py`
- `tests/test_schema_tools.py`

**Why**: These enable reading biosamples from MongoDB and transforming them to schemas. Not needed for simple `get_environmental_metadata()` use case. Olivia's feedback: "what does it mean to get X for/from a biosample" - this complexity is the problem.

**Restoration**: Move back from `archived/mongodb/` when ready to implement Issue #189 (NMDC Submission Schema Transformer)

### Phase 2: Metrics/Evaluation Framework (Future Development)

**Files to move to `archived/metrics/`:**
- `biosample_enricher/metrics/` entire directory (1,752 lines)
  - `evaluator.py` (617 lines)
  - `reporter.py` (165 lines)
  - `visualizer.py` (176 lines)
  - `dashboard.py` (12 lines)
  - `markdown.py` (102 lines)
  - `aligner.py` (147 lines)
  - `fetcher.py` (53 lines)
  - `__init__.py` (16 lines)
- `biosample_enricher/cli_metrics.py` (180 lines)
- Related test files

**Why**: This is for evaluating enrichment quality across large datasets. Not needed for basic value retrieval. Adds ~2,000 lines of distraction.

**Restoration**: Move back when ready to build quality metrics (related to Issues #185, #186)

### Phase 3: Individual Service CLIs (8 CLIs → 1 CLI)

**Files to move to `archived/cli/`:**
- `biosample_enricher/cli_elevation.py` (124 lines)
- `biosample_enricher/cli_soil.py` (214 lines)
- `biosample_enricher/cli_marine.py` (174 lines)
- `biosample_enricher/cli_land.py` (143 lines)
- `biosample_enricher/cli_weather.py` (163 lines)
- `biosample_enricher/cli_forward_geocoding.py` (237 lines)
- `biosample_enricher/cli_osm_features.py` (276 lines)
- `biosample_enricher/cli_biosample_elevation.py` (217 lines)

**Keep only:**
- `biosample_enricher/cli.py` - Main entry point for submission values

**Why**: Multiple CLIs = multiple ways to do things. Violates "one way to do anything" principle. Users should use `get_environmental_metadata()` function, not 8 different CLIs.

**Restoration**: Move back if we decide service-level CLIs are valuable for advanced users.

### Phase 4: Demo/Example Code

**Files to move to `archived/demos/`:**
- `biosample_enricher/elevation_demos.py` (138 lines)
- Any other `*_demo.py` files

**Why**: Examples should be in documentation, not as importable code.

**Restoration**: Convert to Jupyter notebooks or documentation examples.

### Phase 5: Utility Modules (Maybe - TBD)

**Candidates to move to `archived/utils/`:**
- `biosample_enricher/providers.py` (86 lines) - Old provider registry?
- `biosample_enricher/cache_management.py` (98 lines) - If not actively used

**Why**: If these are legacy or not used by `get_environmental_metadata()`, archive them.

**Restoration**: Move back if needed.

## What Stays (Core Functionality)

### Submission Values (Primary API)
- `biosample_enricher/submission_values.py` ⭐ **THE MAIN API**
- `biosample_enricher/cli.py` - CLI wrapper for submission_values

### Core Infrastructure (Required)
- `biosample_enricher/__init__.py`
- `biosample_enricher/_version.py`
- `biosample_enricher/paths.py`
- `biosample_enricher/logging_config.py`
- `biosample_enricher/http_cache.py`
- `biosample_enricher/models.py`

### Service Modules (Used by submission_values)
- `biosample_enricher/weather/` - For climate normals (annual_precpt, annual_temp)
- `biosample_enricher/elevation/` - For elev slot
- `biosample_enricher/marine/` - For depth slot
- `biosample_enricher/soil/` - For ph, soil_type slots
- `biosample_enricher/land/` - Future: cur_vegetation
- `biosample_enricher/forward_geocoding/` - Future use
- `biosample_enricher/reverse_geocoding/` - Future use
- `biosample_enricher/osm_features/` - Future use

**Note**: Services stay because they're the implementation of `get_environmental_metadata()`. They're just not documented as user-facing APIs.

### Tests (Keep all)
- `tests/` - All tests stay, just move archived code's tests to `archived/`

## Implementation Steps

### Step 1: Create Archive Structure
```bash
mkdir -p archived/mongodb
mkdir -p archived/metrics
mkdir -p archived/cli
mkdir -p archived/demos
mkdir -p archived/utils
```

### Step 2: Create Archive README
Write `archived/README.md` explaining:
- Why each directory was archived
- How to restore files
- What GitHub issues relate to each archive
- When we might restore them

### Step 3: Move Files
```bash
# MongoDB/schema
git mv biosample_enricher/adapters.py archived/mongodb/
git mv biosample_enricher/schema_inference.py archived/mongodb/
git mv biosample_enricher/schema_statistics.py archived/mongodb/
git mv biosample_enricher/biosample_elevation_mapper.py archived/mongodb/
git mv tests/test_adapters.py archived/mongodb/
git mv tests/test_schema_tools.py archived/mongodb/

# Metrics
git mv biosample_enricher/metrics archived/metrics/
git mv biosample_enricher/cli_metrics.py archived/metrics/

# CLIs
git mv biosample_enricher/cli_elevation.py archived/cli/
git mv biosample_enricher/cli_soil.py archived/cli/
git mv biosample_enricher/cli_marine.py archived/cli/
git mv biosample_enricher/cli_land.py archived/cli/
git mv biosample_enricher/cli_weather.py archived/cli/
git mv biosample_enricher/cli_forward_geocoding.py archived/cli/
git mv biosample_enricher/cli_osm_features.py archived/cli/
git mv biosample_enricher/cli_biosample_elevation.py archived/cli/

# Demos
git mv biosample_enricher/elevation_demos.py archived/demos/
```

### Step 4: Update Configuration

**In `pyproject.toml`**: Remove CLI entry points for archived CLIs

**In `docs/source/conf.py`**:
```python
exclude_patterns = ['archived']
```

**In `scripts/generate_api_index.py`**:
```python
# Skip archived, __pycache__, and test files
if "archived" in str(py_file) or "__pycache__" in str(py_file) or "test_" in py_file.name:
    continue
```

### Step 5: Fix Imports (If Any)

Search for any imports of archived code:
```bash
grep -r "from biosample_enricher.adapters" biosample_enricher/
grep -r "from biosample_enricher.metrics" biosample_enricher/
# etc.
```

Remove or update any imports of archived code.

### Step 6: Run Tests
```bash
uv run pytest
uv run mypy biosample_enricher
uv run ruff check biosample_enricher
```

Ensure nothing breaks.

### Step 7: Update Documentation

- Remove archived modules from any documentation
- Regenerate API index
- Update homepage to focus on submission_values
- Deploy new docs

### Step 8: Commit
```bash
git add -A
git commit -m "Archive future-development code to focus on NMDC submissions

Moved to archived/:
- MongoDB/schema alignment (adapters, schema_inference, etc.)
- Metrics/evaluation framework (metrics/ directory)
- Individual service CLIs (8 CLIs → keep only main cli.py)
- Demo code (elevation_demos.py)

Why: Simplify focus on core use case - getting NMDC submission values.
Users should use get_environmental_metadata(), not navigate 8 different CLIs
and MongoDB integration that isn't ready yet.

Restoration: See archived/README.md for how to restore each component.

Related to Issue #204 (shift focus to NMDC submissions)
"
```

## Impact Assessment

### Lines of Code Reduction
- **Before**: ~9,718 lines in biosample_enricher/
- **After**: ~5,000 lines (estimate)
- **Archived**: ~4,700 lines (48% reduction)

### Documentation Clarity
- API Index: 412 entries → ~250 entries (remove archived module items)
- User confusion: "8 specialized services" → "1 function for NMDC submissions"
- Navigation: Complex service hierarchy → Simple submission-first docs

### Breaking Changes
- **CLI commands removed**: 8 archived CLIs no longer available
  - Mitigation: Document in CHANGELOG, point to `get_environmental_metadata()`
- **Import errors**: If anyone imports `biosample_enricher.adapters`, etc.
  - Mitigation: Search codebase first, should be minimal external usage

### Restoration Effort
- **Easy**: Just `git mv` files back from `archived/`
- **Time**: ~5 minutes per module
- **Risk**: Low - files are version controlled, just moved

## Questions Before Proceeding

1. **Phase all at once or incrementally?**
   - All at once: Clean break, clear message
   - Incremental: Less risky, test between phases

2. **Keep archived code in git or separate branch?**
   - In git at `archived/`: Easy to restore, clear history
   - Separate branch: Cleaner main branch, harder to restore

3. **Update pyproject.toml optional dependencies?**
   - Keep `[metrics]` extra even though code is archived?
   - Remove it and document how to restore?

4. **What about examples/ directory?**
   - Keep: It's not installed as part of the package
   - Archive: Move to `archived/examples/`
   - Convert: Turn into documentation pages

## Success Criteria

After archiving, a new user (like Olivia) should:

1. Land on docs homepage
2. See "Get NMDC Submission Values" prominently
3. Copy-paste one example with `get_environmental_metadata()`
4. Get their values
5. Never wonder "what does it mean to get X for/from a biosample"

The complexity of MongoDB integration, metrics frameworks, and multiple service APIs should be invisible unless specifically sought out.
