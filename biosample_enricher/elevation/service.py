"""Main elevation service orchestrator."""

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from ..logging_config import get_logger
from ..models import (
    CoordinateClassification,
    ElevationRequest,
    ElevationResult,
    EnrichmentRun,
    FetchResult,
    GeoPoint,
    Observation,
    OutputEnvelope,
    ProviderRef,
    ValueStatus,
    Variable,
)
from .classifier import CoordinateClassifier
from .providers import (
    ElevationProvider,
    GoogleElevationProvider,
    OpenTopoDataProvider,
    OSMElevationProvider,
    USGSElevationProvider,
)
from .utils import calculate_distance_m

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = get_logger(__name__)


class ElevationService:
    """Orchestrates elevation lookups across multiple providers."""

    def __init__(
        self,
        google_api_key: str | None = None,
        enable_google: bool = True,
        enable_usgs: bool = True,
        enable_osm: bool = True,
        enable_open_topo_data: bool = True,
        osm_endpoint: str = "https://api.open-elevation.com/api/v1/lookup",
        open_topo_data_endpoint: str = "https://api.opentopodata.org/v1",
    ) -> None:
        """
        Initialize the elevation service.

        Args:
            google_api_key: Google API key (if None, reads from env)
            enable_google: Whether to enable Google provider
            enable_usgs: Whether to enable USGS provider
            enable_osm: Whether to enable OSM provider
            enable_open_topo_data: Whether to enable Open Topo Data provider
            osm_endpoint: OSM provider endpoint URL
            open_topo_data_endpoint: Open Topo Data endpoint URL
        """
        self.classifier = CoordinateClassifier()
        self.providers: dict[str, ElevationProvider] = {}

        # Initialize providers based on configuration
        if enable_google:
            try:
                self.providers["google"] = GoogleElevationProvider(
                    api_key=google_api_key
                )
                logger.info("Google Elevation provider enabled")
            except ValueError as e:
                logger.warning(f"Google provider disabled: {e}")

        if enable_usgs:
            self.providers["usgs"] = USGSElevationProvider()
            logger.info("USGS Elevation provider enabled")

        if enable_osm:
            self.providers["osm"] = OSMElevationProvider(endpoint=osm_endpoint)
            logger.info("OSM Elevation provider enabled")

        if enable_open_topo_data:
            self.providers["open_topo_data"] = OpenTopoDataProvider(
                endpoint=open_topo_data_endpoint
            )
            logger.info("Open Topo Data provider enabled")

        if not self.providers:
            raise ValueError("No elevation providers are enabled")

        logger.info(
            f"ElevationService initialized with {len(self.providers)} providers"
        )

    @classmethod
    def from_env(cls) -> "ElevationService":
        """
        Create elevation service from environment variables.

        Returns:
            Configured elevation service
        """
        return cls(
            google_api_key=os.getenv("GOOGLE_MAIN_API_KEY"),
            enable_google=os.getenv("ELEVATION_ENABLE_GOOGLE", "true").lower()
            == "true",
            enable_usgs=os.getenv("ELEVATION_ENABLE_USGS", "true").lower() == "true",
            enable_osm=os.getenv("ELEVATION_ENABLE_OSM", "true").lower() == "true",
            enable_open_topo_data=os.getenv(
                "ELEVATION_ENABLE_OPEN_TOPO_DATA", "true"
            ).lower()
            == "true",
            osm_endpoint=os.getenv(
                "ELEVATION_OSM_ENDPOINT", "https://api.open-elevation.com/api/v1/lookup"
            ),
            open_topo_data_endpoint=os.getenv(
                "ELEVATION_OPEN_TOPO_DATA_ENDPOINT", "https://api.opentopodata.org/v1"
            ),
        )

    def classify_coordinates(self, lat: float, lon: float) -> CoordinateClassification:
        """
        Classify coordinates for provider routing.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Coordinate classification
        """
        return self.classifier.classify(lat, lon)

    def classify_biosample_location(self, lat: float, lon: float) -> dict:
        """
        Classify a biosample location for routing and metadata.

        This method provides biosample-specific classification that can be
        stored with the sample metadata for efficient provider routing.

        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees

        Returns:
            Dictionary with classification metadata
        """
        return self.classifier.classify_biosample_location(lat, lon)

    def select_providers(
        self,
        classification: CoordinateClassification,
        preferred: list[str] | None = None,
    ) -> list[ElevationProvider]:
        """
        Select providers based on coordinate classification.

        Args:
            classification: Coordinate classification result
            preferred: Preferred provider names in order

        Returns:
            List of providers in priority order
        """
        available_providers = list(self.providers.keys())

        # Smart routing based on classification
        if classification.is_us_territory:
            if classification.is_land is False:
                # Ocean areas - USGS likely won't work
                default_order = ["google", "open_topo_data", "osm", "usgs"]
            else:
                # US land: USGS first, then others
                default_order = ["usgs", "google", "open_topo_data", "osm"]
        else:
            # International locations
            if classification.is_land is False:
                # International ocean - prioritize global providers
                default_order = ["google", "open_topo_data", "osm"]
            else:
                # International land - Open Topo Data has good global coverage
                default_order = ["google", "open_topo_data", "osm"]

        # Apply preferred providers if specified
        if preferred:
            # Filter preferred to only available providers
            preferred_available = [p for p in preferred if p in available_providers]
            # Add remaining providers not in preferred list
            remaining = [
                p
                for p in default_order
                if p not in preferred_available and p in available_providers
            ]
            provider_order = preferred_available + remaining
        else:
            provider_order = [p for p in default_order if p in available_providers]

        # Return provider objects
        selected = [self.providers[name] for name in provider_order]

        logger.debug(f"Selected providers: {[p.name for p in selected]}")
        return selected

    async def get_elevation(
        self,
        request: ElevationRequest,
        *,
        read_from_cache: bool = True,
        write_to_cache: bool = True,
        timeout_s: float = 20.0,
    ) -> list[Observation]:
        """
        Get elevation observations from multiple providers.

        Args:
            request: Elevation request
            read_from_cache: Whether to read from cache
            write_to_cache: Whether to write to cache
            timeout_s: Request timeout in seconds

        Returns:
            List of elevation observations
        """
        lat, lon = request.latitude, request.longitude

        logger.info(f"Getting elevation for {lat:.6f}, {lon:.6f}")

        # Classify coordinates
        classification = self.classify_coordinates(lat, lon)

        # Select providers
        providers = self.select_providers(classification, request.preferred_providers)

        # Create request location
        request_location = GeoPoint(lat=lat, lon=lon, precision_digits=6)

        observations = []

        for provider in providers:
            try:
                logger.debug(f"Fetching from {provider.name}")

                # Fetch from provider
                result = await provider.fetch(
                    lat,
                    lon,
                    read_from_cache=read_from_cache,
                    write_to_cache=write_to_cache,
                    timeout_s=timeout_s,
                )

                # Convert to observation
                observation = self._create_observation(
                    request_location, provider, result
                )
                observations.append(observation)

                if result.ok:
                    logger.debug(
                        f"{provider.name} returned elevation: {result.elevation}m"
                    )
                else:
                    logger.warning(f"{provider.name} failed: {result.error}")

            except Exception as e:
                logger.error(f"Error fetching from {provider.name}: {e}")

                # Create error observation
                error_observation = self._create_error_observation(
                    request_location, provider, str(e)
                )
                observations.append(error_observation)

        logger.info(f"Completed elevation lookup: {len(observations)} observations")
        return observations

    def get_best_elevation(
        self, observations: list[Observation]
    ) -> ElevationResult | None:
        """
        Select the best elevation from multiple observations.

        Args:
            observations: List of elevation observations

        Returns:
            Best elevation result, or None if no valid observations
        """
        # Filter to successful observations
        valid_obs = [
            obs
            for obs in observations
            if obs.value_status == ValueStatus.OK and obs.value_numeric is not None
        ]

        if not valid_obs:
            return None

        # Sort by distance to input, then by resolution (smaller is better)
        def sort_key(obs: Observation) -> tuple[float, float]:
            distance = obs.distance_to_input_m or 0.0
            resolution = obs.spatial_resolution_m or 999999.0
            return (distance, resolution)

        best_obs = min(valid_obs, key=sort_key)

        # Create classification from first observation (they should all be the same)
        classification = CoordinateClassification(
            is_us_territory=True,  # This would need to be stored in observation
            confidence=1.0,
        )

        return ElevationResult(
            latitude=best_obs.request_location.lat,
            longitude=best_obs.request_location.lon,
            elevation_meters=best_obs.value_numeric or 0.0,
            provider=best_obs.provider.name,
            accuracy_meters=best_obs.spatial_resolution_m,
            data_source=best_obs.provider.name,
            timestamp=best_obs.created_at or datetime.now(UTC),
            classification=classification,
        )

    def create_output_envelope(
        self,
        subject_id: str,
        observations: list[Observation],
        read_from_cache: bool = True,
        write_to_cache: bool = True,
    ) -> OutputEnvelope:
        """
        Create output envelope with observations.

        Args:
            subject_id: Subject identifier
            observations: List of observations
            read_from_cache: Whether cache was used for reading
            write_to_cache: Whether cache was used for writing

        Returns:
            Output envelope
        """
        run = EnrichmentRun(
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            tool_version="biosample-enricher 0.1.0",
            read_from_cache=read_from_cache,
            write_to_cache=write_to_cache,
        )

        return OutputEnvelope(
            schema_version="1.0.0",
            run=run,
            subject_id=subject_id,
            observations=observations,
        )

    def _create_observation(
        self,
        request_location: GeoPoint,
        provider: ElevationProvider,
        result: FetchResult,
    ) -> Observation:
        """Create observation from fetch result."""
        # Calculate distance if measurement location is different
        distance_m = None
        if result.location:
            distance_m = calculate_distance_m(
                request_location.lat,
                request_location.lon,
                result.location.lat,
                result.location.lon,
            )

        # Create request ID
        request_id = self._create_request_id(
            provider.name, request_location.lat, request_location.lon
        )

        # Calculate payload hash
        payload_hash = None
        if result.raw:
            payload_str = json.dumps(result.raw, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        return Observation(
            variable=Variable.ELEVATION,
            value_numeric=result.elevation,
            unit_ucum="m",
            value_status=ValueStatus.OK if result.ok else ValueStatus.ERROR,
            provider=ProviderRef(
                name=provider.name,
                endpoint=provider.endpoint,
                api_version=provider.api_version,
            ),
            request_location=request_location,
            measurement_location=result.location,
            distance_to_input_m=distance_m,
            spatial_resolution_m=result.resolution_m,
            vertical_datum=result.vertical_datum,
            raw_payload=json.dumps(result.raw) if result.raw else None,
            raw_payload_sha256=payload_hash,
            normalization_version="elev-2025-09-10",
            cache_used=False,  # This would need to be passed from provider
            request_id=request_id,
            error_message=result.error if not result.ok else None,
            created_at=datetime.now(UTC),
        )

    def _create_error_observation(
        self,
        request_location: GeoPoint,
        provider: ElevationProvider,
        error_message: str,
    ) -> Observation:
        """Create error observation."""
        request_id = self._create_request_id(
            provider.name, request_location.lat, request_location.lon
        )

        return Observation(
            variable=Variable.ELEVATION,
            value_status=ValueStatus.ERROR,
            provider=ProviderRef(
                name=provider.name,
                endpoint=provider.endpoint,
                api_version=provider.api_version,
            ),
            request_location=request_location,
            normalization_version="elev-2025-09-10",
            request_id=request_id,
            error_message=error_message,
            created_at=datetime.now(UTC),
        )

    def _create_request_id(self, provider_name: str, lat: float, lon: float) -> str:
        """Create deterministic request ID."""
        key = f"{provider_name}:{lat:.6f},{lon:.6f}"
        return hashlib.sha1(key.encode()).hexdigest()[:8]
