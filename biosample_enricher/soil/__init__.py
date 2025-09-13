"""Soil enrichment module for biosample environmental context.

Provides static soil site characterization including:
- Soil taxonomy (USDA/WRB classification systems)
- Soil properties (pH, organic carbon, texture)
- Soil chemistry (nitrogen, phosphorus)
- Texture classification (USDA 12-class system)

This module focuses on site descriptors rather than temporal dynamics.
For daily soil conditions (moisture, temperature), see weather enrichment.
"""

from biosample_enricher.soil.service import SoilService

__all__ = ["SoilService"]
