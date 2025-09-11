"""Host association detection for biosample data.

This module provides utilities for detecting whether a biosample is
host-associated (e.g., human gut, plant rhizosphere) or environmental
(e.g., soil, water, air).
"""

from pathlib import Path
from typing import Any

import yaml

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class HostDetector:
    """Detects host association in biosample data."""

    def __init__(self, config_file: Path | None = None):
        """Initialize host detector with configuration.

        Args:
            config_file: Path to host detection configuration YAML
        """
        if config_file is None:
            config_file = (
                Path(__file__).parent.parent / "config" / "host_detection.yaml"
            )

        with open(config_file) as f:
            self.config = yaml.safe_load(f)

        # Convert keywords to lowercase for case-insensitive matching
        self.host_keywords = [k.lower() for k in self.config.get("host_keywords", [])]
        self.nmdc_fields = self.config.get("nmdc_host_fields", [])
        self.gold_fields = self.config.get("gold_host_fields", [])
        self.host_ecosystem_paths = self.config.get("gold_host_ecosystem_paths", [])
        self.environmental_paths = self.config.get("environmental_ecosystem_paths", [])
        self.host_envo_terms = set(self.config.get("host_envo_terms", []))

        logger.debug(
            f"Loaded host detection config with {len(self.host_keywords)} keywords"
        )

    def is_host_associated_nmdc(self, data: dict[str, Any]) -> bool:
        """Detect if NMDC sample is host-associated.

        Args:
            data: NMDC biosample document

        Returns:
            True if sample appears to be host-associated
        """
        # Check ENVO terms if present
        envo_fields = ["env_broad_scale", "env_local_scale", "env_medium"]
        for field in envo_fields:
            value = data.get(field)
            if value:
                value_lower = str(value).lower()
                # Check against keywords
                for keyword in self.host_keywords:
                    if keyword in value_lower:
                        logger.debug(f"Host keyword '{keyword}' found in {field}")
                        return True
                # Check against ENVO terms
                # Handle NMDC's complex nested structure: {"term": {"id": "...", "name": "..."}}
                envo_term_text = None
                if isinstance(value, dict):
                    # Try to extract the term text from nested structure
                    term_obj = value.get("term")
                    if isinstance(term_obj, dict):
                        # Get the name or ID from the term object
                        envo_term_text = term_obj.get("name") or term_obj.get("id")
                    else:
                        # Fallback to other possible structures
                        envo_term_text = (
                            value.get("has_raw_value")
                            or value.get("name")
                            or str(value)
                        )
                else:
                    envo_term_text = str(value) if value else None

                # Only check if we have a string term
                if (
                    envo_term_text
                    and isinstance(envo_term_text, str)
                    and envo_term_text in self.host_envo_terms
                ):
                    logger.debug(f"Host ENVO term found: {envo_term_text}")
                    return True

        # Check other descriptive fields
        for field_name in self.nmdc_fields:
            if field_name in envo_fields:
                continue  # Already checked

            value = data.get(field_name)
            if value:
                value_lower = str(value).lower()
                for keyword in self.host_keywords:
                    if keyword in value_lower:
                        logger.debug(f"Host keyword '{keyword}' found in {field_name}")
                        return True

        # Check for direct host fields
        host_specific_fields = [
            "host_name",
            "host_taxid",
            "host_common_name",
            "host_subject_id",
            "host_body_site",
            "host_body_habitat",
        ]
        for field in host_specific_fields:
            if data.get(field):
                logger.debug(f"Host-specific field present: {field}")
                return True

        return False

    def is_host_associated_gold(self, data: dict[str, Any]) -> bool:
        """Detect if GOLD sample is host-associated.

        Args:
            data: GOLD biosample document

        Returns:
            True if sample appears to be host-associated
        """
        # Check ecosystem path first (most reliable for GOLD)
        ecosystem_path = data.get("ecosystemPath") or data.get("ecosystem_path") or ""
        ecosystem_path_str = str(ecosystem_path)

        # Check for explicit host-associated paths
        for host_path in self.host_ecosystem_paths:
            if ecosystem_path_str.startswith(host_path):
                logger.debug(f"Host ecosystem path detected: {ecosystem_path_str}")
                return True

        # Check if it's explicitly environmental
        for env_path in self.environmental_paths:
            if ecosystem_path_str.startswith(env_path):
                logger.debug(f"Environmental path detected: {ecosystem_path_str}")
                return False

        # Check ecosystem path for keywords
        ecosystem_lower = ecosystem_path_str.lower()
        for keyword in self.host_keywords:
            if keyword in ecosystem_lower:
                logger.debug(f"Host keyword '{keyword}' found in ecosystem path")
                return True

        # Check other GOLD fields
        for field_name in self.gold_fields:
            if field_name in ["ecosystemPath", "ecosystem_path"]:
                continue  # Already checked

            value = data.get(field_name)
            if value:
                value_lower = str(value).lower()
                for keyword in self.host_keywords:
                    if keyword in value_lower:
                        logger.debug(f"Host keyword '{keyword}' found in {field_name}")
                        return True

        # Check for direct host fields
        host_specific_fields = [
            "hostName",
            "host_name",
            "hostScientificName",
            "hostCommonName",
            "host_common_name",
            "hostTaxonomyId",
            "host_taxid",
        ]
        for field in host_specific_fields:
            if data.get(field):
                logger.debug(f"Host-specific field present: {field}")
                return True

        return False

    def is_host_associated(self, data: dict[str, Any], source: str) -> bool:
        """Detect if a biosample is host-associated.

        Args:
            data: Biosample document
            source: Data source ('nmdc' or 'gold')

        Returns:
            True if sample appears to be host-associated
        """
        if source.lower() == "nmdc":
            return self.is_host_associated_nmdc(data)
        elif source.lower() == "gold":
            return self.is_host_associated_gold(data)
        else:
            logger.warning(f"Unknown source: {source}")
            return False

    def classify_sample_type(self, data: dict[str, Any], source: str) -> str:
        """Classify the sample type based on available metadata.

        Args:
            data: Biosample document
            source: Data source ('nmdc' or 'gold')

        Returns:
            Sample type classification string
        """
        if self.is_host_associated(data, source):
            # Try to be more specific about host type
            text_to_check = []

            if source.lower() == "nmdc":
                for field in ["env_broad_scale", "env_local_scale", "env_medium"]:
                    if data.get(field):
                        text_to_check.append(str(data[field]).lower())
            elif source.lower() == "gold" and data.get("ecosystemPath"):
                text_to_check.append(str(data["ecosystemPath"]).lower())

            combined_text = " ".join(text_to_check)

            # Check for specific host types
            if any(k in combined_text for k in ["human", "clinical", "patient"]):
                return "host-associated:human"
            elif any(
                k in combined_text for k in ["plant", "rhizosphere", "phyllosphere"]
            ):
                return "host-associated:plant"
            elif any(k in combined_text for k in ["animal", "mouse", "rat"]):
                return "host-associated:animal"
            else:
                return "host-associated:other"
        else:
            # Try to classify environmental type
            if source.lower() == "gold":
                ecosystem = str(data.get("ecosystemPath", "")).lower()
                if "marine" in ecosystem:
                    return "environmental:marine"
                elif "freshwater" in ecosystem:
                    return "environmental:freshwater"
                elif "soil" in ecosystem:
                    return "environmental:soil"
                elif "air" in ecosystem:
                    return "environmental:air"

            return "environmental:other"


# Singleton instance for use across the application
_detector = None


def get_host_detector() -> HostDetector:
    """Get or create the singleton host detector instance.

    Returns:
        HostDetector instance
    """
    global _detector
    if _detector is None:
        _detector = HostDetector()
    return _detector
