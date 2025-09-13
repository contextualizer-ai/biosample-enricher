# Configuration Files

This directory contains configuration files used across the biosample-enricher application.

## Files

### `field_mappings.yaml`
Maps fields between different biosample schemas (NMDC, GOLD) and enrichment outputs.
- Defines how to extract equivalent fields from different sources
- Specifies extraction types (direct, nested, array_index, parsing)
- Lists data types for metrics reporting

### `host_detection.yaml`
Configuration for detecting host-associated samples.
- Keywords that indicate host association (gut, rhizosphere, clinical, etc.)
- Fields to check in NMDC and GOLD samples
- ENVO terms that indicate host association
- Ecosystem paths for classification

## Usage

These configuration files are loaded by the application at runtime:

```python
# Host detection
from biosample_enricher.host_detector import get_host_detector
detector = get_host_detector()
is_host = detector.is_host_associated(sample_data, "nmdc")

# Field alignment
from biosample_enricher.metrics.aligner import FieldAligner
aligner = FieldAligner()
extracted = aligner.extract_all_fields(document, "nmdc")
```

## Modifying Configurations

To add new keywords, fields, or mappings:
1. Edit the appropriate YAML file
2. No code changes required - configurations are loaded at runtime
3. Test with sample data to ensure correct detection/mapping

## Future Enhancements

- Add more ENVO term mappings
- Expand host detection patterns
- Add confidence scores for host detection
- Support for additional data sources beyond NMDC/GOLD
