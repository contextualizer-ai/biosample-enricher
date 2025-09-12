"""Marine data providers for oceanographic APIs."""

from biosample_enricher.marine.providers.base import MarineProviderBase
from biosample_enricher.marine.providers.esa_cci import ESACCIProvider
from biosample_enricher.marine.providers.gebco import GEBCOProvider
from biosample_enricher.marine.providers.noaa_oisst import NOAAOISSTProvider

__all__ = ["MarineProviderBase", "GEBCOProvider", "NOAAOISSTProvider", "ESACCIProvider"]
