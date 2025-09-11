"""Elevation data providers."""

from biosample_enricher.elevation.providers.base import ElevationProvider
from biosample_enricher.elevation.providers.google import GoogleElevationProvider
from biosample_enricher.elevation.providers.open_topo_data import (
    OpenTopoDataProvider,
    SmartOpenTopoDataProvider,
)
from biosample_enricher.elevation.providers.osm import OSMElevationProvider
from biosample_enricher.elevation.providers.usgs import USGSElevationProvider

__all__ = [
    "ElevationProvider",
    "GoogleElevationProvider",
    "OpenTopoDataProvider",
    "SmartOpenTopoDataProvider",
    "OSMElevationProvider",
    "USGSElevationProvider",
]
