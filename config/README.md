# Configuration Files

This directory contains the comprehensive configuration system for the biosample-enricher application. All configuration and mapping data has been externalized from hardcoded values to provide flexibility, maintainability, and the foundation for automated configuration generation.

## Configuration Architecture

The configuration system follows a **minimal formats, maximal organization** principle:
- **Single format**: All configs use YAML for consistency and readability
- **Logical separation**: Each file has a specific, focused purpose
- **Hierarchical structure**: Related settings are grouped logically
- **Environment integration**: Sensitive data goes in `.env`, everything else in YAML

## Configuration Files

### Core Configuration

#### `field_mappings.yaml` ✅ *Extended*
Complete field mapping system between NMDC, GOLD, and enrichment outputs.
- **Field priorities**: Order-dependent lists for field extraction
- **Mapping rules**: How to extract and transform field values  
- **ID mappings**: Cross-database identifier relationships
- **Parsing configs**: Coordinate and date parsing specifications
- **Data types**: Field categorization for metrics reporting

#### `host_detection.yaml` ✅ *Existing*
Host association detection configuration.
- **Keywords**: Terms indicating host association
- **Field mappings**: Where to look in NMDC vs GOLD
- **ENVO terms**: Ontology-based detection rules
- **Ecosystem paths**: Hierarchical classification

### Provider and External Services

#### `providers.yaml` 🆕 *New*
Complete API provider configuration.
- **Endpoints**: All API URLs externalized from code
- **Timeouts**: Per-provider timeout and retry settings
- **Rate limits**: Request throttling configurations
- **Provider priority**: Fallback order for services
- **Feature flags**: Enable/disable providers individually

#### `databases.yaml` 🆕 *New*  
Database connection and collection configuration.
- **Connection settings**: MongoDB timeouts and pool sizes
- **Collection mappings**: Database and collection names
- **Query patterns**: Common aggregation pipelines
- **Cache configuration**: HTTP cache policies
- **Environment variables**: Connection string mappings

### Validation and Quality

#### `validation.yaml` 🆕 *New*
Data validation rules and quality thresholds.
- **Coordinate validation**: Lat/lon ranges and precision
- **Date validation**: Format patterns and ranges
- **Coverage thresholds**: Quality assessment criteria
- **Provider health**: Success rate monitoring
- **Data cleaning**: Automatic validation and correction

#### `defaults.yaml` 🆕 *New*
Application defaults and processing parameters.
- **File paths**: Directory structure and naming patterns
- **Sample sizes**: Default values for all operations
- **Processing limits**: Memory, timeout, and batch limits
- **Development settings**: Test coordinates and debug options

## Environment Variables (`.env`)

Sensitive and deployment-specific configuration:
```bash
# Database connections (required)
NMDC_MONGO_CONNECTION="mongodb://user:pass@host:27778/..."
GOLD_MONGO_CONNECTION="mongodb://user:pass@host:27778/..."
CACHE_MONGO_CONNECTION="mongodb://localhost:27017/..."

# API keys (optional)
GOOGLE_MAIN_API_KEY="your_api_key"

# Operational settings
LOG_LEVEL="INFO"
CACHE_ENABLED="true"
```

See `.env.example` for complete template.

## Usage

### Loading Configuration

```python
# Automatic configuration loading
from biosample_enricher.config import get_config

# Get provider settings
config = get_config()
google_endpoint = config.providers.elevation.google.endpoint
timeout = config.providers.elevation.google.timeout_s

# Get database settings  
nmdc_collection = config.databases.nmdc.collections.biosamples
```

### Environment Integration

```python
import os
from biosample_enricher.config import get_database_connection

# Automatic environment variable resolution
nmdc_conn = get_database_connection("nmdc")  # Uses NMDC_MONGO_CONNECTION
google_key = os.getenv("GOOGLE_MAIN_API_KEY")
```

### Field Mapping Usage

```python
from biosample_enricher.config import get_field_mappings

mappings = get_field_mappings()
location_fields = mappings.field_priorities.location_text.nmdc
# Returns: ["geo_loc_name", "geographic_location", "location", ...]
```

## Configuration Benefits

### 🎯 **Flexibility**
- Runtime configuration changes without code redeployment
- Environment-specific settings (dev/staging/prod)
- Easy A/B testing of different provider configurations

### 🔧 **Maintainability** 
- Single source of truth for all configuration
- Self-documenting YAML with comments
- Version control for configuration changes

### 🤖 **Automation Ready**
- Foundation for automated configuration generation
- Schema-driven configuration validation
- Integration with ontology lookup services (OLS)

### 🧪 **Testability**
- Easy mocking with test configurations
- Isolated testing of individual components
- Configuration validation in CI/CD

## Future Automation

This configuration structure is designed to support:

1. **Schema-driven generation**: Auto-generate mappings from `data/outputs/schema/*` files
2. **Ontology integration**: Pull mappings from OLS (Ontology Lookup Service)
3. **Conditional logic**: Dynamic configurations based on categorical field values
4. **Validation workflows**: Automated configuration testing and validation

## Modifying Configurations

### Adding New Fields
1. Add mapping rules to `field_mappings.yaml`
2. Update validation rules in `validation.yaml` if needed
3. No code changes required - configurations are loaded at runtime

### Adding New Providers
1. Add provider config to `providers.yaml`
2. Add any validation rules to `validation.yaml`
3. Implement provider class following existing patterns

### Environment Changes
1. Update `.env` with new variables
2. Add defaults to `.env.example`
3. Document in `databases.yaml` environment mappings

## Validation

Configuration files can be validated:
```bash
# Validate YAML syntax
yamllint config/

# Test configuration loading
uv run python -c "from biosample_enricher.config import validate_config; validate_config()"
```