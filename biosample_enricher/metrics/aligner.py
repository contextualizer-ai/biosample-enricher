"""Field alignment and normalization for cross-schema comparison.

This module handles the complex task of aligning fields from NMDC, GOLD,
and enrichment outputs to enable meaningful comparisons.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class FieldAligner:
    """Aligns fields across different biosample schemas for comparison."""

    def __init__(self, mappings_file: Path | None = None):
        """Initialize field aligner with mappings configuration.

        Args:
            mappings_file: Path to YAML file with field mappings
        """
        if mappings_file is None:
            mappings_file = (
                Path(__file__).parent.parent.parent / "config" / "field_mappings.yaml"
            )

        with open(mappings_file) as f:
            self.mappings = yaml.safe_load(f)

        logger.info(f"Loaded field mappings from {mappings_file}")

    def extract_field_value(
        self, document: dict[str, Any], path: str, extract_type: str = "direct"
    ) -> Any:
        """Extract a field value from a document using a path specification.

        Args:
            document: The source document
            path: Path to the field (e.g., "lat_lon[0]" or "location.latitude")
            extract_type: Type of extraction (direct, nested, array_index, etc.)

        Returns:
            The extracted value or None if not found
        """
        if not document:
            return None

        try:
            if extract_type == "direct":
                return document.get(path)

            elif extract_type == "nested":
                # Navigate nested path like "location.latitude"
                value: Any = document
                for part in path.split("."):
                    if value is None:
                        return None
                    value = value.get(part) if isinstance(value, dict) else None
                return value

            elif extract_type == "array_index":
                # Handle array indexing like "lat_lon[0]"
                match = re.match(r"(\w+)\[(\d+)\]", path)
                if match:
                    field_name, index = match.groups()
                    array = document.get(field_name)
                    if isinstance(array, list | tuple) and len(array) > int(index):
                        return array[int(index)]
                return None

            elif extract_type == "parse_first":
                # Parse first part of colon-separated value (e.g., "USA: California")
                parse_value: Any = document.get(path)
                if parse_value and ":" in str(parse_value):
                    return str(parse_value).split(":")[0].strip()
                return parse_value

            elif extract_type == "parse_second":
                # Parse second part of colon-separated value
                parse_value2: Any = document.get(path)
                if parse_value2 and ":" in str(parse_value2):
                    parts = str(parse_value2).split(":")
                    if len(parts) > 1:
                        return parts[1].strip()
                return None

            elif extract_type == "parse_country":
                # Extract country from various location formats
                country_value: Any = document.get(path)
                if country_value:
                    # Handle "Country: State" format
                    if ":" in str(country_value):
                        return str(country_value).split(":")[0].strip()
                    # Handle "City, State, Country" format
                    elif "," in str(country_value):
                        parts = str(country_value).split(",")
                        return parts[-1].strip() if parts else country_value
                return country_value

            else:
                logger.warning(f"Unknown extract_type: {extract_type}")
                return None

        except Exception as e:
            logger.debug(f"Error extracting {path} from document: {e}")
            return None

    def extract_all_fields(
        self, document: dict[str, Any], source: str
    ) -> dict[str, Any]:
        """Extract all mapped fields from a document.

        Args:
            document: The source document
            source: Source type ('nmdc', 'gold', or 'enrichment')

        Returns:
            Dictionary of extracted field values organized by category
        """
        extracted: dict[str, Any] = {}

        for category, fields in self.mappings.items():
            if category == "data_types":
                continue  # Skip metadata

            extracted[category] = {}

            for field_name, field_mappings in fields.items():
                if source not in field_mappings:
                    continue

                # Try each possible path for this field
                value = None
                for path_spec in field_mappings[source]:
                    if isinstance(path_spec, dict):
                        path = path_spec.get("path")
                        extract_type = path_spec.get("type", "direct")
                    else:
                        path = path_spec
                        extract_type = "direct"

                    if path and isinstance(path, str):
                        value = self.extract_field_value(document, path, extract_type)
                        if value is not None:
                            break  # Use first non-null value

                extracted[category][field_name] = value

        return extracted

    def compare_fields(
        self, before_doc: dict[str, Any], after_doc: dict[str, Any], source: str
    ) -> dict[str, dict[str, Any]]:
        """Compare field coverage before and after enrichment.

        Args:
            before_doc: Original document
            after_doc: Enriched document
            source: Source type ('nmdc' or 'gold')

        Returns:
            Comparison results organized by data type
        """
        # Extract fields from both documents
        before_fields = self.extract_all_fields(before_doc, source)
        after_fields = self.extract_all_fields(after_doc, "enrichment")

        # Merge enriched fields with original
        # (enrichment might not have all original fields)
        for category in before_fields:
            if category not in after_fields:
                after_fields[category] = {}
            for field in before_fields[category]:
                if field not in after_fields[category]:
                    # Keep original value if enrichment doesn't provide it
                    after_fields[category][field] = before_fields[category][field]

        # Compare and generate metrics
        comparisons = {}

        for data_type_spec in self.mappings.get("data_types", []):
            data_type_name = data_type_spec["name"]
            category = data_type_spec["category"]

            # Handle multiple fields for a data type (e.g., Place Name)
            if "fields" in data_type_spec:
                field_names = data_type_spec["fields"]
            else:
                field_names = [data_type_spec["field"]]

            # Check if any of the fields have values
            before_values = []
            after_values = []

            for field_name in field_names:
                before_val = before_fields.get(category, {}).get(field_name)
                after_val = after_fields.get(category, {}).get(field_name)

                if before_val is not None:
                    before_values.append(before_val)
                if after_val is not None:
                    after_values.append(after_val)

            comparisons[data_type_name] = {
                "before": len(before_values) > 0,
                "after": len(after_values) > 0,
                "before_values": before_values,
                "after_values": after_values,
                "improved": len(after_values) > len(before_values),
                "category": category,
            }

        return comparisons

    def normalize_value(self, value: Any, field_type: str | None = None) -> Any:
        """Normalize a field value for comparison.

        Args:
            value: The value to normalize
            field_type: Optional type hint for normalization

        Returns:
            Normalized value
        """
        if value is None:
            return None

        # Normalize strings
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ["", "null", "none", "n/a", "na", "unknown"]:
                return None
            return value

        # Normalize numbers
        if field_type == "temperature" and value is not None:
            # Could convert F to C or vice versa here
            return float(value)

        if field_type == "elevation" and value is not None:
            # Could convert feet to meters here
            return float(value)

        return value

    def align_temporal_data(
        self, collection_date: str | None, api_date: str | None, tolerance_days: int = 7
    ) -> bool:
        """Check if temporal data is aligned within tolerance.

        Args:
            collection_date: Sample collection date
            api_date: Date from API response
            tolerance_days: Maximum days difference to consider aligned

        Returns:
            True if dates are aligned within tolerance
        """
        if not collection_date or not api_date:
            return False

        try:
            from datetime import datetime

            # Parse dates (handle various formats)
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    date1 = datetime.strptime(str(collection_date)[:10], fmt)
                    break
                except ValueError:
                    continue
            else:
                return False

            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    date2 = datetime.strptime(str(api_date)[:10], fmt)
                    break
                except ValueError:
                    continue
            else:
                return False

            # Check if within tolerance
            diff = abs((date1 - date2).days)
            return diff <= tolerance_days

        except Exception as e:
            logger.debug(f"Error aligning temporal data: {e}")
            return False
