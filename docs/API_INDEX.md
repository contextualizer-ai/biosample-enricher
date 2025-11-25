# Alphabetical API Index

This is a comprehensive alphabetical index of all public functions and methods in the biosample-enricher package.

---

## A

### `analyze`

- **Type**: function
- **Module**: `cli_biosample_elevation`
- **Signature**: `analyze(input_file: Path) -> None`
- **Description**: Analyze biosample field mapping without performing elevation lookups.

### `analyze`

- **Type**: function
- **Module**: `cli_weather`
- **Signature**: `analyze(input_file: str, source: str, output_dir: str | None, sample_limit: int | None)`
- **Description**: Analyze weather enrichment coverage for a collection of biosamples.

## B

### `BaseElevationProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.base`
- **Class**: `BaseElevationProvider`
- **Signature**: `__init__(self, name: str, endpoint: str, api_version: str) -> None`
- **Description**: Initialize the provider.

### `BaseElevationProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.base`
- **Class**: `BaseElevationProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data for the given coordinates.

### `BaseReverseGeocodingProvider.__init__`

- **Type**: method
- **Module**: `reverse_geocoding.providers.base`
- **Class**: `BaseReverseGeocodingProvider`
- **Signature**: `__init__(self, name: str, endpoint: str, api_version: str) -> None`
- **Description**: Initialize the provider.

### `BaseReverseGeocodingProvider.fetch`

- **Type**: method
- **Module**: `reverse_geocoding.providers.base`
- **Class**: `BaseReverseGeocodingProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> ReverseGeocodeFetchResult`
- **Description**: Fetch reverse geocoding data for the given coordinates.

### `batch`

- **Type**: function
- **Module**: `cli_soil`
- **Signature**: `batch(input_file: Path, output: Path, depth: str, lat_col: str, lon_col: str, output_format: str, verbose: bool) -> None`
- **Description**: Enrich multiple locations from CSV or JSON file.

### `batch`

- **Type**: function
- **Module**: `cli_land`
- **Signature**: `batch(input_file: str, date: datetime | None, time_window: int, output: str, batch_size: int)`
- **Description**: Process multiple locations from a file.

### `batch`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `batch(input_file: str, language: str, output: str, batch_size: int)`
- **Description**: Process multiple place names from a file.

### `batch`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `batch(input_file: str, radius: int, timeout: int, output: str, batch_size: int)`
- **Description**: Process multiple locations from a file.

### `batch`

- **Type**: function
- **Module**: `cli_marine`
- **Signature**: `batch(input: str, output: str | None, schema: str, max_samples: int | None)`
- **Description**: Batch marine enrichment for multiple biosamples.

### `batch_elevation`

- **Type**: function
- **Module**: `cli_elevation`
- **Signature**: `batch_elevation(input_file: Path, output: str, providers: tuple[str, ...], timeout: float, lat_col: str, lon_col: str, id_col: str, no_cache: bool, read_cache: bool, write_cache: bool) -> None`
- **Description**: Process elevation lookups from CSV/TSV file.

### `BiosampleAdapter.extract_location`

- **Type**: method
- **Module**: `adapters`
- **Class**: `BiosampleAdapter`
- **Signature**: `extract_location(self, biosample_data: dict[str, Any]) -> BiosampleLocation`
- **Description**: Extract standardized location data from a single biosample.

### `BiosampleAdapter.extract_locations_batch`

- **Type**: method
- **Module**: `adapters`
- **Class**: `BiosampleAdapter`
- **Signature**: `extract_locations_batch(self, biosamples: list[dict[str, Any]]) -> list[BiosampleLocation]`
- **Description**: Extract location data from multiple biosamples.

### `BiosampleElevationBatch.filter_valid_coordinates`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationBatch`
- **Signature**: `filter_valid_coordinates(biosamples: list[dict[str, Any]]) -> list[dict[str, Any]]`
- **Description**: Filter biosamples to only those with valid coordinates.

### `BiosampleElevationBatch.get_coordinate_summary`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationBatch`
- **Signature**: `get_coordinate_summary(biosamples: list[dict[str, Any]]) -> dict[str, Any]`
- **Description**: Get summary statistics about coordinates in a biosample collection.

### `BiosampleElevationMapper.create_elevation_request`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `create_elevation_request(biosample: dict[str, Any], preferred_providers: list[str] | None) -> ElevationRequest | None`
- **Description**: Create an ElevationRequest from biosample metadata.

### `BiosampleElevationMapper.extract_coordinates`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `extract_coordinates(biosample: dict[str, Any]) -> tuple[float, float] | None`
- **Description**: Extract latitude and longitude from various biosample field structures.

### `BiosampleElevationMapper.get_biosample_id`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `get_biosample_id(biosample: dict[str, Any]) -> str`
- **Description**: Extract a unique identifier from biosample metadata.

### `BiosampleElevationMapper.get_field_mapping_info`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `get_field_mapping_info() -> dict[str, Any]`
- **Description**: Get comprehensive information about biosample field mappings.

### `BiosampleElevationMapper.get_location_context`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `get_location_context(biosample: dict[str, Any]) -> dict[str, Any]`
- **Description**: Extract additional location context from biosample metadata.

### `BiosampleElevationMapper.validate_coordinates`

- **Type**: method
- **Module**: `biosample_elevation_mapper`
- **Class**: `BiosampleElevationMapper`
- **Signature**: `validate_coordinates(lat: float, lon: float) -> bool`
- **Description**: Validate that coordinates are within valid ranges.

### `BiosampleLocation.calculate_completeness`

- **Type**: method
- **Module**: `models`
- **Class**: `BiosampleLocation`
- **Signature**: `calculate_completeness(self) -> 'BiosampleLocation'`
- **Description**: Calculate location completeness score based on available fields.

### `BiosampleLocation.is_enrichable`

- **Type**: method
- **Module**: `models`
- **Class**: `BiosampleLocation`
- **Signature**: `is_enrichable(self) -> bool`
- **Description**: Check if sample has minimum data for API enrichment.

### `BiosampleLocation.to_dict`

- **Type**: method
- **Module**: `models`
- **Class**: `BiosampleLocation`
- **Signature**: `to_dict(self) -> dict`
- **Description**: Convert to dictionary for serialization with enrichable status.

### `BiosampleLocation.validate_collection_date`

- **Type**: method
- **Module**: `models`
- **Class**: `BiosampleLocation`
- **Signature**: `validate_collection_date(cls, v: str | None) -> str | None`
- **Description**: Validate collection date format.

### `BiosampleMetricsFetcher.__init__`

- **Type**: method
- **Module**: `metrics.fetcher`
- **Class**: `BiosampleMetricsFetcher`
- **Signature**: `__init__(self, nmdc_connection_string: str | None, gold_connection_string: str | None, nmdc_database: str, gold_database: str, nmdc_collection: str, gold_collection: str)`
- **Description**: Initialize metrics fetcher with database connections.

### `BiosampleMetricsFetcher.fetch_all_samples`

- **Type**: method
- **Module**: `metrics.fetcher`
- **Class**: `BiosampleMetricsFetcher`
- **Signature**: `fetch_all_samples(self, n_per_source: int, enrichable_only: bool) -> dict[str, tuple[list[dict[str, Any]], list[BiosampleLocation]]]`
- **Description**: Fetch random samples from both NMDC and GOLD.

### `BiosampleMetricsFetcher.fetch_gold_samples`

- **Type**: method
- **Module**: `metrics.fetcher`
- **Class**: `BiosampleMetricsFetcher`
- **Signature**: `fetch_gold_samples(self, n: int, enrichable_only: bool) -> tuple[list[dict[str, Any]], list[BiosampleLocation]]`
- **Description**: Fetch random GOLD samples.

### `BiosampleMetricsFetcher.fetch_nmdc_samples`

- **Type**: method
- **Module**: `metrics.fetcher`
- **Class**: `BiosampleMetricsFetcher`
- **Signature**: `fetch_nmdc_samples(self, n: int, enrichable_only: bool) -> tuple[list[dict[str, Any]], list[BiosampleLocation]]`
- **Description**: Fetch random NMDC samples.

## C

### `calculate_distance_m`

- **Type**: function
- **Module**: `elevation.utils`
- **Signature**: `calculate_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float`
- **Description**: Calculate the great circle distance between two points using the Haversine formula.

### `canonicalize_coords`

- **Type**: function
- **Module**: `http_cache`
- **Signature**: `canonicalize_coords(params: dict[str, Any]) -> dict[str, Any]`
- **Description**: Canonicalize coordinate parameters for consistent caching.

### `classify_texture`

- **Type**: function
- **Module**: `soil.models`
- **Signature**: `classify_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str`
- **Description**: Classify soil texture using USDA texture triangle.

### `clear`

- **Type**: function
- **Module**: `cache_management`
- **Signature**: `clear(ctx: click.Context, confirm: bool) -> None`
- **Description**: Clear all cache entries.

### `cli`

- **Type**: function
- **Module**: `cache_management`
- **Signature**: `cli(ctx: click.Context) -> None`
- **Description**: HTTP Cache Management CLI.

### `cli`

- **Type**: function
- **Module**: `elevation_demos`
- **Signature**: `cli(log_level: str) -> None`
- **Description**: Elevation service demonstrations and batch processing.

### `cli`

- **Type**: function
- **Module**: `cli_biosample_elevation`
- **Signature**: `cli(log_level: str) -> None`
- **Description**: Biosample elevation enrichment CLI with automatic field mapping.

### `ClimateNormalsResult.get_annual_precipitation`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `ClimateNormalsResult`
- **Signature**: `get_annual_precipitation(self) -> float | None`
- **Description**: Calculate annual precipitation by summing 12 monthly normals.

### `ClimateNormalsResult.get_annual_temperature`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `ClimateNormalsResult`
- **Signature**: `get_annual_temperature(self) -> float | None`
- **Description**: Calculate annual average temperature from 12 monthly normals.

### `ClimateNormalsResult.to_submission_schema`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `ClimateNormalsResult`
- **Signature**: `to_submission_schema(self) -> dict[str, Any]`
- **Description**: Extract values in submission-schema compatible format.

### `CombinedFeaturesResult.to_enrichment_dict`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `CombinedFeaturesResult`
- **Signature**: `to_enrichment_dict(self) -> dict[str, Any]`
- **Description**: Convert combined results to enrichment dictionary.

### `compare`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `compare(query: str, language: str, country: str | None, max_results: int, output: str | None, pretty: bool)`
- **Description**: Compare results from all available providers.

### `compare_providers`

- **Type**: function
- **Module**: `elevation_demos`
- **Signature**: `compare_providers(lat: float, lon: float, providers: str, output: str) -> None`
- **Description**: Compare elevation results from different providers for a single coordinate.

### `configure_from_env`

- **Type**: function
- **Module**: `logging_config`
- **Signature**: `configure_from_env() -> logging.Logger`
- **Description**: Configure logging from environment variables.

### `CoordinateClassifier.__init__`

- **Type**: method
- **Module**: `elevation.classifier`
- **Class**: `CoordinateClassifier`
- **Signature**: `__init__(self, enable_online_detection: bool, user_agent: str) -> None`
- **Description**: Initialize the coordinate classifier.

### `CoordinateClassifier.classify`

- **Type**: method
- **Module**: `elevation.classifier`
- **Class**: `CoordinateClassifier`
- **Signature**: `classify(self, lat: float, lon: float) -> CoordinateClassification`
- **Description**: Classify coordinates to determine appropriate providers.

### `CoordinateClassifier.classify_biosample_location`

- **Type**: method
- **Module**: `elevation.classifier`
- **Class**: `CoordinateClassifier`
- **Signature**: `classify_biosample_location(self, lat: float, lon: float) -> dict`
- **Description**: Classify a biosample location for routing and metadata.

### `CoverageEvaluator.__init__`

- **Type**: method
- **Module**: `metrics.evaluator`
- **Class**: `CoverageEvaluator`
- **Signature**: `__init__(self) -> None`
- **Description**: Initialize evaluator with enrichment services.

### `CoverageEvaluator.evaluate_batch`

- **Type**: method
- **Module**: `metrics.evaluator`
- **Class**: `CoverageEvaluator`
- **Signature**: `evaluate_batch(self, samples: list[tuple[dict[str, Any], BiosampleLocation]], source: str) -> list[dict[str, Any]]`
- **Description**: Evaluate a batch of samples.

### `CoverageEvaluator.evaluate_sample`

- **Type**: method
- **Module**: `metrics.evaluator`
- **Class**: `CoverageEvaluator`
- **Signature**: `evaluate_sample(self, raw_doc: dict[str, Any], normalized_location: BiosampleLocation, source: str) -> dict[str, Any]`
- **Description**: Evaluate a single sample for coverage metrics.

## D

### `demo`

- **Type**: function
- **Module**: `cli_weather`
- **Signature**: `demo()`
- **Description**: Run weather enrichment demonstration.

### `demonstrate_field_mapping`

- **Type**: function
- **Module**: `biosample_elevation_mapper`
- **Signature**: `demonstrate_field_mapping() -> None`
- **Description**: Demonstrate the field mapping capabilities with example data.

## E

### `elevation_cli`

- **Type**: function
- **Module**: `cli_elevation`
- **Signature**: `elevation_cli(log_level: str) -> None`
- **Description**: Elevation lookup CLI.

### `ElevationProvider.choices`

- **Type**: method
- **Module**: `providers`
- **Class**: `ElevationProvider`
- **Signature**: `choices(cls) -> list[str]`
- **Description**: Get list of provider choices for Click.

### `ElevationProvider.description`

- **Type**: method
- **Module**: `providers`
- **Class**: `ElevationProvider`
- **Signature**: `description(cls) -> str`
- **Description**: Get formatted description of all available providers.

### `ElevationProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.base`
- **Class**: `ElevationProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data for the given coordinates.

### `ElevationProvider.info`

- **Type**: method
- **Module**: `providers`
- **Class**: `ElevationProvider`
- **Signature**: `info(cls, provider: 'ElevationProvider | str') -> ProviderInfo`
- **Description**: Get detailed information about a provider.

### `ElevationService.__init__`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `__init__(self, google_api_key: str | None, enable_google: bool, enable_usgs: bool, enable_osm: bool, enable_open_topo_data: bool, osm_endpoint: str, open_topo_data_endpoint: str) -> None`
- **Description**: Initialize the elevation service.

### `ElevationService.classify_biosample_location`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `classify_biosample_location(self, lat: float, lon: float) -> dict`
- **Description**: Classify a biosample location for routing and metadata.

### `ElevationService.classify_coordinates`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `classify_coordinates(self, lat: float, lon: float) -> CoordinateClassification`
- **Description**: Classify coordinates for provider routing.

### `ElevationService.create_output_envelope`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `create_output_envelope(self, subject_id: str, observations: list[Observation], read_from_cache: bool, write_to_cache: bool) -> OutputEnvelope`
- **Description**: Create output envelope with observations.

### `ElevationService.from_env`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `from_env(cls) -> 'ElevationService'`
- **Description**: Create elevation service from environment variables.

### `ElevationService.get_best_elevation`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `get_best_elevation(self, observations: list[Observation]) -> ElevationResult | None`
- **Description**: Select the best elevation from multiple observations.

### `ElevationService.get_elevation`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `get_elevation(self, request: ElevationRequest) -> list[Observation]`
- **Description**: Get elevation observations from multiple providers.

### `ElevationService.select_providers`

- **Type**: method
- **Module**: `elevation.service`
- **Class**: `ElevationService`
- **Signature**: `select_providers(self, classification: CoordinateClassification, preferred: list[str] | None) -> list[ElevationProvider]`
- **Description**: Select providers based on coordinate classification.

### `enrich`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `enrich(query: str, language: str, country: str | None)`
- **Description**: Get coordinates and enrichment data for biosample place names.

### `enrich`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `enrich(latitude: float, longitude: float, radius: int, timeout: int, providers: str)`
- **Description**: Get enrichment data for biosample coordinates.

### `enrich`

- **Type**: function
- **Module**: `cli_biosample_elevation`
- **Signature**: `enrich(input_file: Path, output: Path, output_format: str, timeout: float, no_cache: bool, providers: tuple[str, ...], show_mapping: bool) -> None`
- **Description**: Enrich biosamples with elevation data using automatic field mapping.

### `ESACCIProvider.__init__`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `__init__(self, timeout: int) -> None`
- **Description**: Initialize ESA CCI provider.

### `ESACCIProvider.get_coverage_period`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Get temporal coverage.

### `ESACCIProvider.get_marine_data`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `get_marine_data(self, latitude: float, longitude: float, target_date: date, _parameters: list[str] | None) -> MarineResult`
- **Description**: Get chlorophyll-a data from ESA CCI.

### `ESACCIProvider.get_provider_info`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `get_provider_info(self) -> dict[str, Any]`
- **Description**: Get ESA CCI provider information.

### `ESACCIProvider.is_available`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `is_available(self, latitude: float, longitude: float, target_date: date) -> bool`
- **Description**: Check if ESA CCI data is available for location and date.

### `ESACCIProvider.provider_name`

- **Type**: method
- **Module**: `marine.providers.esa_cci`
- **Class**: `ESACCIProvider`
- **Signature**: `provider_name(self) -> str`
- **Description**: Get provider name.

### `ESAWorldCoverProvider.__init__`

- **Type**: method
- **Module**: `land.providers.esa_worldcover`
- **Class**: `ESAWorldCoverProvider`
- **Signature**: `__init__(self, timeout: int)`

### `ESAWorldCoverProvider.coverage_description`

- **Type**: method
- **Module**: `land.providers.esa_worldcover`
- **Class**: `ESAWorldCoverProvider`
- **Signature**: `coverage_description(self) -> str`

### `ESAWorldCoverProvider.get_land_cover`

- **Type**: method
- **Module**: `land.providers.esa_worldcover`
- **Class**: `ESAWorldCoverProvider`
- **Signature**: `get_land_cover(self, latitude: float, longitude: float, target_date: date | None) -> list[LandCoverObservation]`
- **Description**: Get ESA WorldCover land cover data.

### `ESAWorldCoverProvider.is_available`

- **Type**: method
- **Module**: `land.providers.esa_worldcover`
- **Class**: `ESAWorldCoverProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if ESA WorldCover WMS is available.

### `ESAWorldCoverProvider.name`

- **Type**: method
- **Module**: `land.providers.esa_worldcover`
- **Class**: `ESAWorldCoverProvider`
- **Signature**: `name(self) -> str`

### `evaluate`

- **Type**: function
- **Module**: `cli_metrics`
- **Signature**: `evaluate(nmdc_samples: int, gold_samples: int, exclude_host: bool, output_dir: Path, nmdc_connection: str | None, gold_connection: str | None, create_plots: bool, verbose: bool, debug_samples: bool, enrichment_lifecycle_dir: Path) -> None`
- **Description**: Evaluate enrichment coverage metrics for random samples.

## F

### `FieldAligner.__init__`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `__init__(self, mappings_file: Path | None)`
- **Description**: Initialize field aligner with mappings configuration.

### `FieldAligner.align_temporal_data`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `align_temporal_data(self, collection_date: str | None, api_date: str | None, tolerance_days: int) -> bool`
- **Description**: Check if temporal data is aligned within tolerance.

### `FieldAligner.compare_fields`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `compare_fields(self, before_doc: dict[str, Any], after_doc: dict[str, Any], source: str) -> dict[str, dict[str, Any]]`
- **Description**: Compare field coverage before and after enrichment.

### `FieldAligner.extract_all_fields`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `extract_all_fields(self, document: dict[str, Any], source: str) -> dict[str, Any]`
- **Description**: Extract all mapped fields from a document.

### `FieldAligner.extract_field_value`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `extract_field_value(self, document: dict[str, Any], path: str, extract_type: str) -> Any`
- **Description**: Extract a field value from a document using a path specification.

### `FieldAligner.normalize_value`

- **Type**: method
- **Module**: `metrics.aligner`
- **Class**: `FieldAligner`
- **Signature**: `normalize_value(self, value: Any, field_type: str | None) -> Any`
- **Description**: Normalize a field value for comparison.

### `FileBiosampleFetcher.__init__`

- **Type**: method
- **Module**: `adapters`
- **Class**: `FileBiosampleFetcher`
- **Signature**: `__init__(self, file_path: str | Path, format_type: str)`

### `FileBiosampleFetcher.detect_format`

- **Type**: method
- **Module**: `adapters`
- **Class**: `FileBiosampleFetcher`
- **Signature**: `detect_format(self) -> str`
- **Description**: Detect file format and biosample type.

### `FileBiosampleFetcher.fetch_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `FileBiosampleFetcher`
- **Signature**: `fetch_locations(self, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch locations from file (stub implementation).

### `forward_geocoding`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `forward_geocoding()`
- **Description**: Forward geocoding commands - convert place names to coordinates.

### `ForwardGeocodeResult.get_administrative_summary`

- **Type**: method
- **Module**: `forward_geocoding.models`
- **Class**: `ForwardGeocodeResult`
- **Signature**: `get_administrative_summary(self) -> dict[str, str]`
- **Description**: Get administrative components from best match.

### `ForwardGeocodeResult.get_best_match`

- **Type**: method
- **Module**: `forward_geocoding.models`
- **Class**: `ForwardGeocodeResult`
- **Signature**: `get_best_match(self) -> ForwardGeocodeLocation | None`
- **Description**: Get the highest relevance/confidence location result.

### `ForwardGeocodeResult.get_coordinates`

- **Type**: method
- **Module**: `forward_geocoding.models`
- **Class**: `ForwardGeocodeResult`
- **Signature**: `get_coordinates(self) -> tuple[float, float] | None`
- **Description**: Get coordinates from best match.

### `ForwardGeocodeResult.to_enrichment_dict`

- **Type**: method
- **Module**: `forward_geocoding.models`
- **Class**: `ForwardGeocodeResult`
- **Signature**: `to_enrichment_dict(self) -> dict[str, Any]`
- **Description**: Convert to dictionary suitable for biosample coordinate enrichment.

### `ForwardGeocodingProvider.attribution`

- **Type**: method
- **Module**: `forward_geocoding.providers.base`
- **Class**: `ForwardGeocodingProvider`
- **Signature**: `attribution(self) -> str | None`
- **Description**: Required attribution text.

### `ForwardGeocodingProvider.is_available`

- **Type**: method
- **Module**: `forward_geocoding.providers.base`
- **Class**: `ForwardGeocodingProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if provider is available (API key, network, etc.).

### `ForwardGeocodingProvider.name`

- **Type**: method
- **Module**: `forward_geocoding.providers.base`
- **Class**: `ForwardGeocodingProvider`
- **Signature**: `name(self) -> str`
- **Description**: Provider name for identification.

### `ForwardGeocodingProvider.search`

- **Type**: method
- **Module**: `forward_geocoding.providers.base`
- **Class**: `ForwardGeocodingProvider`
- **Signature**: `search(self, query: str) -> ForwardGeocodeFetchResult`
- **Description**: Perform forward geocoding to convert place names to coordinates.

### `ForwardGeocodingProvider.validate_query`

- **Type**: method
- **Module**: `forward_geocoding.providers.base`
- **Class**: `ForwardGeocodingProvider`
- **Signature**: `validate_query(self, query: str) -> None`
- **Description**: Validate place name query input.

### `ForwardGeocodingService.__init__`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `__init__(self) -> None`
- **Description**: Initialize the forward geocoding service.

### `ForwardGeocodingService.geocode`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `geocode(self, query: str, provider: str | None) -> ForwardGeocodeResult | None`
- **Description**: Perform forward geocoding to convert place name to coordinates.

### `ForwardGeocodingService.geocode_multiple`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `geocode_multiple(self, query: str, providers: list[str] | None) -> dict[str, ForwardGeocodeResult]`
- **Description**: Perform forward geocoding using multiple providers for comparison.

### `ForwardGeocodingService.get_available_providers`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `get_available_providers(self) -> list[str]`
- **Description**: Get list of available provider names.

### `ForwardGeocodingService.get_coordinates_for_place`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `get_coordinates_for_place(self, place_name: str, prefer_provider: str | None, language: str, country_hint: str | None) -> dict[str, Any]`
- **Description**: Get coordinates and enrichment data for a biosample place name.

### `ForwardGeocodingService.get_provider`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `get_provider(self, name: str) -> ForwardGeocodingProvider | None`
- **Description**: Get a specific provider by name.

### `ForwardGeocodingService.get_provider_status`

- **Type**: method
- **Module**: `forward_geocoding.service`
- **Class**: `ForwardGeocodingService`
- **Signature**: `get_provider_status(self) -> dict[str, dict[str, Any]]`
- **Description**: Get status information for all providers.

## G

### `GEBCOProvider.__init__`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `__init__(self, timeout: int) -> None`
- **Description**: Initialize GEBCO provider.

### `GEBCOProvider.get_coverage_period`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Get temporal coverage (static dataset).

### `GEBCOProvider.get_marine_data`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `get_marine_data(self, latitude: float, longitude: float, target_date: date, _parameters: list[str] | None) -> MarineResult`
- **Description**: Get bathymetry data from GEBCO.

### `GEBCOProvider.get_provider_info`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `get_provider_info(self) -> dict[str, Any]`
- **Description**: Get GEBCO provider information.

### `GEBCOProvider.is_available`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `is_available(self, latitude: float, longitude: float, _target_date: date) -> bool`
- **Description**: Check if GEBCO data is available for location.

### `GEBCOProvider.provider_name`

- **Type**: method
- **Module**: `marine.providers.gebco`
- **Class**: `GEBCOProvider`
- **Signature**: `provider_name(self) -> str`
- **Description**: Get provider name.

### `generate_html_dashboard`

- **Type**: function
- **Module**: `metrics.dashboard`
- **Signature**: `generate_html_dashboard(summary_csv: Path, regional_csv: Path | None, output_path: Path | None) -> str`
- **Description**: Generate HTML dashboard with embedded data and charts.

### `generate_markdown_table`

- **Type**: function
- **Module**: `metrics.markdown`
- **Signature**: `generate_markdown_table(df: pd.DataFrame) -> str`
- **Description**: Convert DataFrame to GitHub-flavored markdown table.

### `generate_metrics_report`

- **Type**: function
- **Module**: `metrics.markdown`
- **Signature**: `generate_metrics_report(csv_path: Path) -> str`
- **Description**: Generate enrichment performance report showing what data types are enriched.

### `get_config_dir`

- **Type**: function
- **Module**: `paths`
- **Signature**: `get_config_dir() -> Path`
- **Description**: Get the config directory.

### `get_data_dir`

- **Type**: function
- **Module**: `paths`
- **Signature**: `get_data_dir() -> Path`
- **Description**: Get the data directory.

### `get_host_detector`

- **Type**: function
- **Module**: `host_detector`
- **Signature**: `get_host_detector() -> HostDetector`
- **Description**: Get or create the singleton host detector instance.

### `get_logger`

- **Type**: function
- **Module**: `logging_config`
- **Signature**: `get_logger(name: str) -> logging.Logger`
- **Description**: Get a logger instance for a module.

### `get_logs_dir`

- **Type**: function
- **Module**: `paths`
- **Signature**: `get_logs_dir() -> Path`
- **Description**: Get the logs directory.

### `get_package_data_dir`

- **Type**: function
- **Module**: `paths`
- **Signature**: `get_package_data_dir() -> Path`
- **Description**: Get the package data directory.

### `get_project_root`

- **Type**: function
- **Module**: `paths`
- **Signature**: `get_project_root() -> Path`
- **Description**: Get the project root directory.

### `get_session`

- **Type**: function
- **Module**: `http_cache`
- **Signature**: `get_session() -> CachedSession`
- **Description**: Get cached session with SQLite backend.

### `get_submission_values`

- **Type**: function
- **Module**: `submission_values`
- **Signature**: `get_submission_values(lat: float, lon: float, slots: list[str], datetime_obj: datetime | None, providers: list[str] | None) -> dict[str, Any]`
- **Description**: Get NMDC submission-schema compliant values for specified slots.

### `GOLDBiosampleAdapter.extract_location`

- **Type**: method
- **Module**: `adapters`
- **Class**: `GOLDBiosampleAdapter`
- **Signature**: `extract_location(self, biosample_data: dict[str, Any], database: Any) -> BiosampleLocation`
- **Description**: Extract location data from GOLD biosample document.

### `GOLDBiosampleAdapter.extract_locations_batch`

- **Type**: method
- **Module**: `adapters`
- **Class**: `GOLDBiosampleAdapter`
- **Signature**: `extract_locations_batch(self, biosamples: list[dict[str, Any]]) -> list[BiosampleLocation]`
- **Description**: Extract location data from multiple GOLD biosamples.

### `GoogleElevationProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.google`
- **Class**: `GoogleElevationProvider`
- **Signature**: `__init__(self, api_key: str | None) -> None`
- **Description**: Initialize Google Elevation provider.

### `GoogleElevationProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.google`
- **Class**: `GoogleElevationProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data from Google Elevation API.

### `GoogleForwardGeocodingProvider.__init__`

- **Type**: method
- **Module**: `forward_geocoding.providers.google`
- **Class**: `GoogleForwardGeocodingProvider`
- **Signature**: `__init__(self, api_key: str | None)`
- **Description**: Initialize Google provider.

### `GoogleForwardGeocodingProvider.attribution`

- **Type**: method
- **Module**: `forward_geocoding.providers.google`
- **Class**: `GoogleForwardGeocodingProvider`
- **Signature**: `attribution(self) -> str`

### `GoogleForwardGeocodingProvider.is_available`

- **Type**: method
- **Module**: `forward_geocoding.providers.google`
- **Class**: `GoogleForwardGeocodingProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if Google API is available.

### `GoogleForwardGeocodingProvider.name`

- **Type**: method
- **Module**: `forward_geocoding.providers.google`
- **Class**: `GoogleForwardGeocodingProvider`
- **Signature**: `name(self) -> str`

### `GoogleForwardGeocodingProvider.search`

- **Type**: method
- **Module**: `forward_geocoding.providers.google`
- **Class**: `GoogleForwardGeocodingProvider`
- **Signature**: `search(self, query: str) -> ForwardGeocodeFetchResult`
- **Description**: Search for places by name using Google Maps Geocoding API.

### `GooglePlacesProvider.__init__`

- **Type**: method
- **Module**: `osm_features.google_provider`
- **Class**: `GooglePlacesProvider`
- **Signature**: `__init__(self, api_key: str | None)`
- **Description**: Initialize Google Places provider.

### `GooglePlacesProvider.get_features`

- **Type**: method
- **Module**: `osm_features.google_provider`
- **Class**: `GooglePlacesProvider`
- **Signature**: `get_features(self, latitude: float, longitude: float, radius_m: int, timeout_s: int) -> GooglePlacesFetchResult`
- **Description**: Get geographic features from Google Places API.

### `GooglePlacesProvider.is_available`

- **Type**: method
- **Module**: `osm_features.google_provider`
- **Class**: `GooglePlacesProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if Google Places API is available.

### `GooglePlacesResult.get_nearest_feature`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `GooglePlacesResult`
- **Signature**: `get_nearest_feature(self, category: FeatureCategory) -> GooglePlacesFeature | None`
- **Description**: Get nearest feature of specified category.

### `GooglePlacesResult.to_enrichment_dict`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `GooglePlacesResult`
- **Signature**: `to_enrichment_dict(self) -> dict[str, Any]`
- **Description**: Convert to dictionary suitable for biosample enrichment.

### `GoogleReverseGeocodingProvider.__init__`

- **Type**: method
- **Module**: `reverse_geocoding.providers.google`
- **Class**: `GoogleReverseGeocodingProvider`
- **Signature**: `__init__(self, api_key: str | None) -> None`
- **Description**: Initialize Google Geocoding reverse geocoding provider.

### `GoogleReverseGeocodingProvider.fetch`

- **Type**: method
- **Module**: `reverse_geocoding.providers.google`
- **Class**: `GoogleReverseGeocodingProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> ReverseGeocodeFetchResult`
- **Description**: Fetch reverse geocoding data from Google Geocoding API.

## H

### `HostDetector.__init__`

- **Type**: method
- **Module**: `host_detector`
- **Class**: `HostDetector`
- **Signature**: `__init__(self, config_file: Path | None)`
- **Description**: Initialize host detector with configuration.

### `HostDetector.classify_sample_type`

- **Type**: method
- **Module**: `host_detector`
- **Class**: `HostDetector`
- **Signature**: `classify_sample_type(self, data: dict[str, Any], source: str) -> str`
- **Description**: Classify the sample type based on available metadata.

### `HostDetector.is_host_associated`

- **Type**: method
- **Module**: `host_detector`
- **Class**: `HostDetector`
- **Signature**: `is_host_associated(self, data: dict[str, Any], source: str) -> bool`
- **Description**: Detect if a biosample is host-associated.

### `HostDetector.is_host_associated_gold`

- **Type**: method
- **Module**: `host_detector`
- **Class**: `HostDetector`
- **Signature**: `is_host_associated_gold(self, data: dict[str, Any]) -> bool`
- **Description**: Detect if GOLD sample is host-associated.

### `HostDetector.is_host_associated_nmdc`

- **Type**: method
- **Module**: `host_detector`
- **Class**: `HostDetector`
- **Signature**: `is_host_associated_nmdc(self, data: dict[str, Any]) -> bool`
- **Description**: Detect if NMDC sample is host-associated.

## I

### `info`

- **Type**: function
- **Module**: `cache_management`
- **Signature**: `info(ctx: click.Context) -> None`
- **Description**: Show cache information.

## L

### `land`

- **Type**: function
- **Module**: `cli_land`
- **Signature**: `land()`
- **Description**: Land cover and vegetation enrichment commands.

### `LandCoverObservation.validate_location`

- **Type**: method
- **Module**: `land.models`
- **Class**: `LandCoverObservation`
- **Signature**: `validate_location(cls, v: dict[str, float]) -> dict[str, float]`
- **Description**: Validate location coordinates.

### `LandCoverProviderBase.coverage_description`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `LandCoverProviderBase`
- **Signature**: `coverage_description(self) -> str`
- **Description**: Description of geographic and temporal coverage.

### `LandCoverProviderBase.get_land_cover`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `LandCoverProviderBase`
- **Signature**: `get_land_cover(self, latitude: float, longitude: float, target_date: date | None) -> list[LandCoverObservation]`
- **Description**: Retrieve land cover data for a specific location and date.

### `LandCoverProviderBase.is_available`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `LandCoverProviderBase`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if the provider is currently available.

### `LandCoverProviderBase.name`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `LandCoverProviderBase`
- **Signature**: `name(self) -> str`
- **Description**: Provider name for identification and logging.

### `LandCoverProviderBase.validate_coordinates`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `LandCoverProviderBase`
- **Signature**: `validate_coordinates(self, latitude: float, longitude: float) -> None`
- **Description**: Validate coordinate inputs.

### `LandResult.to_gold_schema`

- **Type**: method
- **Module**: `land.models`
- **Class**: `LandResult`
- **Signature**: `to_gold_schema(self) -> dict[str, Any]`
- **Description**: Convert to GOLD schema format.

### `LandResult.to_nmdc_schema`

- **Type**: method
- **Module**: `land.models`
- **Class**: `LandResult`
- **Signature**: `to_nmdc_schema(self) -> dict[str, Any]`
- **Description**: Convert to NMDC schema format.

### `LandResult.validate_requested_location`

- **Type**: method
- **Module**: `land.models`
- **Class**: `LandResult`
- **Signature**: `validate_requested_location(cls, v: dict[str, float]) -> dict[str, float]`
- **Description**: Validate requested location coordinates.

### `LandService.__init__`

- **Type**: method
- **Module**: `land.service`
- **Class**: `LandService`
- **Signature**: `__init__(self)`
- **Description**: Initialize land service with all providers.

### `LandService.enrich_batch`

- **Type**: method
- **Module**: `land.service`
- **Class**: `LandService`
- **Signature**: `enrich_batch(self, locations: list[tuple[float, float]], target_date: date | None, time_window_days: int) -> list[LandResult]`
- **Description**: Enrich multiple locations with land cover and vegetation data.

### `LandService.enrich_biosample`

- **Type**: method
- **Module**: `land.service`
- **Class**: `LandService`
- **Signature**: `enrich_biosample(self, sample_data: dict[str, Any]) -> dict[str, Any]`
- **Description**: Enrich a single biosample with land cover and vegetation data.

### `LandService.enrich_location`

- **Type**: method
- **Module**: `land.service`
- **Class**: `LandService`
- **Signature**: `enrich_location(self, latitude: float, longitude: float, target_date: date | None, time_window_days: int) -> LandResult`
- **Description**: Enrich a single location with land cover and vegetation data.

### `LandService.get_provider_status`

- **Type**: method
- **Module**: `land.service`
- **Class**: `LandService`
- **Signature**: `get_provider_status(self) -> dict[str, dict[str, Any]]`
- **Description**: Get status of all land cover and vegetation providers.

### `LocationDetector.__init__`

- **Type**: method
- **Module**: `elevation.location_detector`
- **Class**: `LocationDetector`
- **Signature**: `__init__(self, user_agent: str)`
- **Description**: Initialize the location detector.

### `LocationDetector.classify_for_elevation_routing`

- **Type**: method
- **Module**: `elevation.location_detector`
- **Class**: `LocationDetector`
- **Signature**: `classify_for_elevation_routing(self, lat: float, lon: float) -> dict[str, Any]`
- **Description**: Classify coordinates specifically for elevation service routing.

### `LocationDetector.detect_location`

- **Type**: method
- **Module**: `elevation.location_detector`
- **Class**: `LocationDetector`
- **Signature**: `detect_location(self, lat: float, lon: float, prefer_online: bool) -> dict[str, Any]`
- **Description**: Detect location characteristics using multiple methods.

### `lookup`

- **Type**: function
- **Module**: `cli_soil`
- **Signature**: `lookup(latitude: float, longitude: float, depth: str, output_format: str, verbose: bool) -> None`
- **Description**: Look up soil data for a specific location.

### `lookup`

- **Type**: function
- **Module**: `cli_land`
- **Signature**: `lookup(lat: float, lon: float, date: datetime | None, time_window: int, output: str | None, pretty: bool)`
- **Description**: Look up land cover and vegetation data for a single location.

### `lookup`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `lookup(query: str, provider: str, language: str, country: str | None, max_results: int, output: str | None, pretty: bool)`
- **Description**: Look up coordinates for a place name.

### `lookup`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `lookup(latitude: float, longitude: float, radius: int, providers: str, timeout: int, output: str | None, pretty: bool)`
- **Description**: Look up geographic features around coordinates.

### `lookup`

- **Type**: function
- **Module**: `cli_marine`
- **Signature**: `lookup(lat: float, lon: float, date: str, providers: str, output: str | None, schema: str)`
- **Description**: Look up marine data for a specific location and date.

### `lookup`

- **Type**: function
- **Module**: `cli_weather`
- **Signature**: `lookup(lat: float, lon: float, date: str, providers: str, output: str | None, schema: str)`
- **Description**: Get weather data for specific coordinates and date.

### `lookup_elevation`

- **Type**: function
- **Module**: `cli_elevation`
- **Signature**: `lookup_elevation(lat: float, lon: float, providers: tuple[str, ...], output: str | None, subject_id: str, timeout: float, no_cache: bool, read_cache: bool, write_cache: bool) -> None`
- **Description**: Look up elevation for a single coordinate.

## M

### `main`

- **Type**: function
- **Module**: `cli`
- **Signature**: `main() -> None`
- **Description**: Biosample Enricher: Infer AI-friendly metadata about biosamples.

### `main`

- **Type**: function
- **Module**: `schema_inference`
- **Signature**: `main() -> None`

### `main`

- **Type**: function
- **Module**: `schema_statistics`
- **Signature**: `main() -> None`

### `marine_cli`

- **Type**: function
- **Module**: `cli_marine`
- **Signature**: `marine_cli(debug: bool)`
- **Description**: Marine enrichment CLI for biosample oceanographic context.

### `MarineObservation.validate_value`

- **Type**: method
- **Module**: `marine.models`
- **Class**: `MarineObservation`
- **Signature**: `validate_value(cls, v)`
- **Description**: Validate observation value.

### `MarineProviderBase.__init__`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `__init__(self, timeout: int) -> None`
- **Description**: Initialize provider with timeout setting.

### `MarineProviderBase.get_coverage_period`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Get temporal coverage of the provider.

### `MarineProviderBase.get_marine_data`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `get_marine_data(self, latitude: float, longitude: float, target_date: date, parameters: list[str] | None) -> MarineResult`
- **Description**: Get marine data for location and date.

### `MarineProviderBase.get_provider_info`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `get_provider_info(self) -> dict[str, Any]`
- **Description**: Get provider metadata and capabilities.

### `MarineProviderBase.is_available`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `is_available(self, latitude: float, longitude: float, target_date: date) -> bool`
- **Description**: Check if provider has data for given location and date.

### `MarineProviderBase.provider_name`

- **Type**: method
- **Module**: `marine.providers.base`
- **Class**: `MarineProviderBase`
- **Signature**: `provider_name(self) -> str`
- **Description**: Get the provider name.

### `MarineResult.get_coverage_metrics`

- **Type**: method
- **Module**: `marine.models`
- **Class**: `MarineResult`
- **Signature**: `get_coverage_metrics(self) -> dict[str, Any]`
- **Description**: Generate coverage metrics for this marine result.

### `MarineResult.get_schema_mapping`

- **Type**: method
- **Module**: `marine.models`
- **Class**: `MarineResult`
- **Signature**: `get_schema_mapping(self, target_schema: str) -> dict[str, Any]`
- **Description**: Map marine data to target biosample schema.

### `MarineResult.validate_date_format`

- **Type**: method
- **Module**: `marine.models`
- **Class**: `MarineResult`
- **Signature**: `validate_date_format(cls, v)`
- **Description**: Validate date format.

### `MarineService.__init__`

- **Type**: method
- **Module**: `marine.service`
- **Class**: `MarineService`
- **Signature**: `__init__(self, providers: list[MarineProviderBase] | None)`
- **Description**: Initialize marine service with provider chain.

### `MarineService.get_comprehensive_marine_data`

- **Type**: method
- **Module**: `marine.service`
- **Class**: `MarineService`
- **Signature**: `get_comprehensive_marine_data(self, latitude: float, longitude: float, target_date: date) -> MarineResult`
- **Description**: Get comprehensive marine data from all available providers.

### `MarineService.get_marine_data_for_biosample`

- **Type**: method
- **Module**: `marine.service`
- **Class**: `MarineService`
- **Signature**: `get_marine_data_for_biosample(self, biosample: dict[str, Any], target_schema: str) -> dict[str, Any]`
- **Description**: Get marine data for a biosample and map to target schema.

### `MeteostatProvider.__init__`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `__init__(self, timeout: int)`

### `MeteostatProvider.get_climate_normals`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_climate_normals(self, lat: float, lon: float, start_year: int, end_year: int) -> ClimateNormalsResult`
- **Description**: Get 30-year climate averages (normals) for a location.

### `MeteostatProvider.get_coverage_period`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Return temporal coverage period.

### `MeteostatProvider.get_daily_weather`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_daily_weather(self, lat: float, lon: float, target_date: date, _parameters: list[str] | None) -> WeatherResult`
- **Description**: Get daily weather data for specific date and location from MeteoStat.

### `MeteostatProvider.get_spatial_resolution`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_spatial_resolution(self) -> str`
- **Description**: Return spatial resolution.

### `MeteostatProvider.get_supported_parameters`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_supported_parameters(self) -> list[str]`
- **Description**: Return list of weather parameters supported by MeteoStat.

### `MeteostatProvider.get_temporal_resolution`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `get_temporal_resolution(self) -> str`
- **Description**: Return temporal resolution.

### `MeteostatProvider.is_available`

- **Type**: method
- **Module**: `weather.providers.meteostat`
- **Class**: `MeteostatProvider`
- **Signature**: `is_available(self, _lat: float, _lon: float, target_date: date) -> bool`
- **Description**: Check if MeteoStat has data for the given location and date.

### `metrics`

- **Type**: function
- **Module**: `cli_metrics`
- **Signature**: `metrics() -> None`
- **Description**: Evaluate enrichment coverage metrics.

### `MetricsReporter.__init__`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `__init__(self, output_dir: Path | None)`
- **Description**: Initialize reporter with output directory.

### `MetricsReporter.generate_detailed_samples`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `generate_detailed_samples(self, evaluations: list[dict[str, Any]], limit: int) -> pd.DataFrame`
- **Description**: Generate detailed per-sample results.

### `MetricsReporter.generate_regional_table`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `generate_regional_table(self, evaluations: list[dict[str, Any]]) -> pd.DataFrame`
- **Description**: Generate coverage table by geographic region.

### `MetricsReporter.generate_summary_table`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `generate_summary_table(self, evaluations: list[dict[str, Any]], exclude_host_associated: bool) -> pd.DataFrame`
- **Description**: Generate overall coverage summary table.

### `MetricsReporter.print_summary`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `print_summary(self, summary_df: pd.DataFrame) -> None`
- **Description**: Print summary table to console.

### `MetricsReporter.save_all_reports`

- **Type**: method
- **Module**: `metrics.reporter`
- **Class**: `MetricsReporter`
- **Signature**: `save_all_reports(self, evaluations: list[dict[str, Any]], prefix: str) -> dict[str, Path]`
- **Description**: Save all report tables to CSV files.

### `MetricsVisualizer.__init__`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `__init__(self, output_dir: Path | None)`
- **Description**: Initialize visualizer with output directory.

### `MetricsVisualizer.create_all_visualizations`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `create_all_visualizations(self, evaluations: list[dict[str, Any]], summary_df: pd.DataFrame, regional_df: pd.DataFrame, prefix: str) -> dict[str, Path]`
- **Description**: Create all visualization plots.

### `MetricsVisualizer.plot_host_association_breakdown`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `plot_host_association_breakdown(self, evaluations: list[dict[str, Any]], save_path: Path | None) -> plt.Figure`
- **Description**: Create pie charts showing host-associated vs environmental samples.

### `MetricsVisualizer.plot_improvement_bars`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `plot_improvement_bars(self, summary_df: pd.DataFrame, save_path: Path | None) -> plt.Figure`
- **Description**: Create bar chart showing improvement percentages.

### `MetricsVisualizer.plot_regional_comparison`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `plot_regional_comparison(self, regional_df: pd.DataFrame, save_path: Path | None) -> plt.Figure`
- **Description**: Create regional comparison plot.

### `MetricsVisualizer.plot_source_datatype_coverage`

- **Type**: method
- **Module**: `metrics.visualizer`
- **Class**: `MetricsVisualizer`
- **Signature**: `plot_source_datatype_coverage(self, summary_df: pd.DataFrame, save_path: Path | None) -> plt.Figure`
- **Description**: Create grouped bar chart for source × data type coverage.

### `MODISVegetationProvider.__init__`

- **Type**: method
- **Module**: `land.providers.modis_vegetation`
- **Class**: `MODISVegetationProvider`
- **Signature**: `__init__(self, timeout: int)`

### `MODISVegetationProvider.coverage_description`

- **Type**: method
- **Module**: `land.providers.modis_vegetation`
- **Class**: `MODISVegetationProvider`
- **Signature**: `coverage_description(self) -> str`

### `MODISVegetationProvider.get_vegetation_indices`

- **Type**: method
- **Module**: `land.providers.modis_vegetation`
- **Class**: `MODISVegetationProvider`
- **Signature**: `get_vegetation_indices(self, latitude: float, longitude: float, target_date: date | None, time_window_days: int) -> list[VegetationObservation]`
- **Description**: Get MODIS vegetation indices.

### `MODISVegetationProvider.is_available`

- **Type**: method
- **Module**: `land.providers.modis_vegetation`
- **Class**: `MODISVegetationProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if APPEEARS API is available.

### `MODISVegetationProvider.name`

- **Type**: method
- **Module**: `land.providers.modis_vegetation`
- **Class**: `MODISVegetationProvider`
- **Signature**: `name(self) -> str`

### `MongoGOLDBiosampleFetcher.__init__`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `__init__(self, connection_string: str | None, database_name: str, collection_name: str)`

### `MongoGOLDBiosampleFetcher.connect`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `connect(self) -> bool`
- **Description**: Establish MongoDB connection.

### `MongoGOLDBiosampleFetcher.count_enrichable_samples`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `count_enrichable_samples(self) -> int`
- **Description**: Count biosamples with coordinates.

### `MongoGOLDBiosampleFetcher.count_total_samples`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `count_total_samples(self) -> int`
- **Description**: Count total biosamples in collection.

### `MongoGOLDBiosampleFetcher.disconnect`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `disconnect(self) -> None`
- **Description**: Close MongoDB connection.

### `MongoGOLDBiosampleFetcher.fetch_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `fetch_enrichable_locations(self, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch only biosamples with coordinates suitable for enrichment.

### `MongoGOLDBiosampleFetcher.fetch_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `fetch_locations(self, query: dict[str, Any] | None, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch and extract locations from GOLD biosamples.

### `MongoGOLDBiosampleFetcher.fetch_locations_by_ids`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `fetch_locations_by_ids(self, ids: list[str], id_field: str) -> Iterator[BiosampleLocation]`
- **Description**: Fetch biosamples by specific IDs using native field names.

### `MongoGOLDBiosampleFetcher.fetch_random_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `fetch_random_enrichable_locations(self, n: int) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random enrichable biosamples from collection.

### `MongoGOLDBiosampleFetcher.fetch_random_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoGOLDBiosampleFetcher`
- **Signature**: `fetch_random_locations(self, n: int) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random biosamples from collection.

### `MongoNMDCBiosampleFetcher.__init__`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `__init__(self, connection_string: str | None, database_name: str, collection_name: str)`

### `MongoNMDCBiosampleFetcher.connect`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `connect(self) -> bool`
- **Description**: Establish MongoDB connection.

### `MongoNMDCBiosampleFetcher.count_enrichable_samples`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `count_enrichable_samples(self) -> int`
- **Description**: Count biosamples with coordinates.

### `MongoNMDCBiosampleFetcher.count_total_samples`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `count_total_samples(self) -> int`
- **Description**: Count total biosamples in collection.

### `MongoNMDCBiosampleFetcher.disconnect`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `disconnect(self) -> None`
- **Description**: Close MongoDB connection.

### `MongoNMDCBiosampleFetcher.fetch_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `fetch_enrichable_locations(self, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch only biosamples with coordinates suitable for enrichment.

### `MongoNMDCBiosampleFetcher.fetch_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `fetch_locations(self, query: dict[str, Any] | None, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch and extract locations from NMDC biosamples.

### `MongoNMDCBiosampleFetcher.fetch_locations_by_ids`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `fetch_locations_by_ids(self, ids: list[str], id_field: str) -> Iterator[BiosampleLocation]`
- **Description**: Fetch biosamples by specific IDs using native field names.

### `MongoNMDCBiosampleFetcher.fetch_random_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `fetch_random_enrichable_locations(self, n: int) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random enrichable biosamples from collection.

### `MongoNMDCBiosampleFetcher.fetch_random_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `MongoNMDCBiosampleFetcher`
- **Signature**: `fetch_random_locations(self, n: int) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random biosamples from collection.

### `MultiProviderClimateNormals.get_consensus_precipitation`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `MultiProviderClimateNormals`
- **Signature**: `get_consensus_precipitation(self) -> float | None`
- **Description**: Calculate consensus annual precipitation across all successful providers.

### `MultiProviderClimateNormals.get_consensus_temperature`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `MultiProviderClimateNormals`
- **Signature**: `get_consensus_temperature(self) -> float | None`
- **Description**: Calculate consensus annual temperature across all successful providers.

### `MultiProviderClimateNormals.get_provider_result`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `MultiProviderClimateNormals`
- **Signature**: `get_provider_result(self, provider_name: str) -> 'ClimateNormalsResult | None'`
- **Description**: Get result from a specific provider.

### `MultiProviderClimateNormals.get_value_ranges`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `MultiProviderClimateNormals`
- **Signature**: `get_value_ranges(self) -> dict[str, tuple[float, float] | None]`
- **Description**: Get min/max range of values across providers.

### `MultiProviderClimateNormals.to_submission_schema`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `MultiProviderClimateNormals`
- **Signature**: `to_submission_schema(self, provider: str | None, strategy: str) -> dict[str, Any]`
- **Description**: Extract values in submission-schema compatible format.

## N

### `NASAPowerProvider.__init__`

- **Type**: method
- **Module**: `weather.providers.nasa_power`
- **Class**: `NASAPowerProvider`
- **Signature**: `__init__(self, timeout: int)`
- **Description**: Initialize NASA POWER provider.

### `NASAPowerProvider.get_climate_normals`

- **Type**: method
- **Module**: `weather.providers.nasa_power`
- **Class**: `NASAPowerProvider`
- **Signature**: `get_climate_normals(self, lat: float, lon: float, start_year: int, end_year: int) -> ClimateNormalsResult`
- **Description**: Get 20-year climate averages from NASA POWER.

### `NLCDProvider.__init__`

- **Type**: method
- **Module**: `land.providers.nlcd`
- **Class**: `NLCDProvider`
- **Signature**: `__init__(self, timeout: int)`

### `NLCDProvider.coverage_description`

- **Type**: method
- **Module**: `land.providers.nlcd`
- **Class**: `NLCDProvider`
- **Signature**: `coverage_description(self) -> str`

### `NLCDProvider.get_land_cover`

- **Type**: method
- **Module**: `land.providers.nlcd`
- **Class**: `NLCDProvider`
- **Signature**: `get_land_cover(self, latitude: float, longitude: float, target_date: date | None) -> list[LandCoverObservation]`
- **Description**: Get NLCD land cover data.

### `NLCDProvider.is_available`

- **Type**: method
- **Module**: `land.providers.nlcd`
- **Class**: `NLCDProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if NLCD WMS is available.

### `NLCDProvider.name`

- **Type**: method
- **Module**: `land.providers.nlcd`
- **Class**: `NLCDProvider`
- **Signature**: `name(self) -> str`

### `NMDCBiosampleAdapter.extract_location`

- **Type**: method
- **Module**: `adapters`
- **Class**: `NMDCBiosampleAdapter`
- **Signature**: `extract_location(self, biosample_data: dict[str, Any]) -> BiosampleLocation`
- **Description**: Extract location data from NMDC biosample document.

### `NMDCBiosampleAdapter.extract_locations_batch`

- **Type**: method
- **Module**: `adapters`
- **Class**: `NMDCBiosampleAdapter`
- **Signature**: `extract_locations_batch(self, biosamples: list[dict[str, Any]]) -> list[BiosampleLocation]`
- **Description**: Extract location data from multiple NMDC biosamples.

### `NOAAOISSTProvider.__init__`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `__init__(self, timeout: int) -> None`
- **Description**: Initialize NOAA OISST provider.

### `NOAAOISSTProvider.get_coverage_period`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Get temporal coverage.

### `NOAAOISSTProvider.get_marine_data`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `get_marine_data(self, latitude: float, longitude: float, target_date: date, _parameters: list[str] | None) -> MarineResult`
- **Description**: Get SST data from NOAA OISST.

### `NOAAOISSTProvider.get_provider_info`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `get_provider_info(self) -> dict[str, Any]`
- **Description**: Get NOAA OISST provider information.

### `NOAAOISSTProvider.is_available`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `is_available(self, latitude: float, longitude: float, target_date: date) -> bool`
- **Description**: Check if OISST data is available for location and date.

### `NOAAOISSTProvider.provider_name`

- **Type**: method
- **Module**: `marine.providers.noaa_oisst`
- **Class**: `NOAAOISSTProvider`
- **Signature**: `provider_name(self) -> str`
- **Description**: Get provider name.

## O

### `OpenMeteoProvider.__init__`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `__init__(self, timeout: int)`

### `OpenMeteoProvider.get_coverage_period`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Return temporal coverage period.

### `OpenMeteoProvider.get_daily_weather`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `get_daily_weather(self, lat: float, lon: float, target_date: date, parameters: list[str] | None) -> WeatherResult`
- **Description**: Get daily weather data for specific date and location from Open-Meteo.

### `OpenMeteoProvider.get_spatial_resolution`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `get_spatial_resolution(self) -> str`
- **Description**: Return spatial resolution.

### `OpenMeteoProvider.get_supported_parameters`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `get_supported_parameters(self) -> list[str]`
- **Description**: Return list of weather parameters supported by Open-Meteo.

### `OpenMeteoProvider.get_temporal_resolution`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `get_temporal_resolution(self) -> str`
- **Description**: Return temporal resolution.

### `OpenMeteoProvider.is_available`

- **Type**: method
- **Module**: `weather.providers.open_meteo`
- **Class**: `OpenMeteoProvider`
- **Signature**: `is_available(self, _lat: float, _lon: float, target_date: date) -> bool`
- **Description**: Check if Open-Meteo has data for the given location and date.

### `OpenTopoDataProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.open_topo_data`
- **Class**: `OpenTopoDataProvider`
- **Signature**: `__init__(self, endpoint: str, dataset: str) -> None`
- **Description**: Initialize Open Topo Data provider.

### `OpenTopoDataProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.open_topo_data`
- **Class**: `OpenTopoDataProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data from Open Topo Data API.

### `osm_features`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `osm_features()`
- **Description**: OpenStreetMap geographic features commands.

### `OSMElevationProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.osm`
- **Class**: `OSMElevationProvider`
- **Signature**: `__init__(self, endpoint: str) -> None`
- **Description**: Initialize OSM-like elevation provider.

### `OSMElevationProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.osm`
- **Class**: `OSMElevationProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data from OpenElevation-style API.

### `OSMFeaturesResult.get_distance_summary`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `OSMFeaturesResult`
- **Signature**: `get_distance_summary(self) -> dict[str, Any]`
- **Description**: Generate distance summary for key feature categories.

### `OSMFeaturesResult.get_feature_counts_by_category`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `OSMFeaturesResult`
- **Signature**: `get_feature_counts_by_category(self) -> dict[str, int]`
- **Description**: Get counts of unnamed features by main category.

### `OSMFeaturesResult.get_features_by_category`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `OSMFeaturesResult`
- **Signature**: `get_features_by_category(self, category: FeatureCategory) -> list[OSMNamedFeature]`
- **Description**: Get all named features of a specific category.

### `OSMFeaturesResult.get_nearest_feature`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `OSMFeaturesResult`
- **Signature**: `get_nearest_feature(self, category: FeatureCategory) -> OSMNamedFeature | None`
- **Description**: Get the nearest named feature of a specific category.

### `OSMFeaturesResult.to_enrichment_dict`

- **Type**: method
- **Module**: `osm_features.models`
- **Class**: `OSMFeaturesResult`
- **Signature**: `to_enrichment_dict(self) -> dict[str, Any]`
- **Description**: Convert to dictionary suitable for biosample enrichment.

### `OSMFeaturesService.__init__`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `__init__(self, default_radius_m: int, enable_google: bool)`
- **Description**: Initialize geographic features service.

### `OSMFeaturesService.batch_enrich_locations`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `batch_enrich_locations(self, locations: list[tuple[float, float]], radius_m: int, timeout_s: int) -> list[dict[str, Any]]`
- **Description**: Batch enrich multiple locations with OSM features.

### `OSMFeaturesService.enrich_biosample_location`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `enrich_biosample_location(self, latitude: float, longitude: float, radius_m: int | None, timeout_s: int, use_combined: bool) -> dict[str, Any]`
- **Description**: Enrich a biosample location with geographic features from multiple providers.

### `OSMFeaturesService.get_combined_features_for_location`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `get_combined_features_for_location(self, latitude: float, longitude: float, radius_m: int | None, timeout_s: int) -> CombinedFeaturesResult`
- **Description**: Get geographic features from both OSM and Google Places providers.

### `OSMFeaturesService.get_features_for_biosample`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `get_features_for_biosample(self, biosample: dict[str, Any], radius_m: int, timeout_s: int) -> dict[str, Any]`
- **Description**: Get OSM features for a biosample dictionary.

### `OSMFeaturesService.get_features_for_location`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `get_features_for_location(self, latitude: float, longitude: float, radius_m: int | None, timeout_s: int) -> OSMFeaturesResult | None`
- **Description**: Get geographic features around a location from OSM only (for backward compatibility).

### `OSMFeaturesService.get_provider_status`

- **Type**: method
- **Module**: `osm_features.service`
- **Class**: `OSMFeaturesService`
- **Signature**: `get_provider_status(self) -> dict[str, Any]`
- **Description**: Get status of all geographic features providers.

### `OSMForwardGeocodingProvider.__init__`

- **Type**: method
- **Module**: `forward_geocoding.providers.osm`
- **Class**: `OSMForwardGeocodingProvider`
- **Signature**: `__init__(self, base_url: str)`
- **Description**: Initialize OSM provider.

### `OSMForwardGeocodingProvider.attribution`

- **Type**: method
- **Module**: `forward_geocoding.providers.osm`
- **Class**: `OSMForwardGeocodingProvider`
- **Signature**: `attribution(self) -> str`

### `OSMForwardGeocodingProvider.is_available`

- **Type**: method
- **Module**: `forward_geocoding.providers.osm`
- **Class**: `OSMForwardGeocodingProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if Nominatim API is available.

### `OSMForwardGeocodingProvider.name`

- **Type**: method
- **Module**: `forward_geocoding.providers.osm`
- **Class**: `OSMForwardGeocodingProvider`
- **Signature**: `name(self) -> str`

### `OSMForwardGeocodingProvider.search`

- **Type**: method
- **Module**: `forward_geocoding.providers.osm`
- **Class**: `OSMForwardGeocodingProvider`
- **Signature**: `search(self, query: str) -> ForwardGeocodeFetchResult`
- **Description**: Search for places by name using OSM Nominatim search API.

### `OSMOverpassProvider.__init__`

- **Type**: method
- **Module**: `osm_features.provider`
- **Class**: `OSMOverpassProvider`
- **Signature**: `__init__(self, base_url: str)`
- **Description**: Initialize OSM Overpass provider.

### `OSMOverpassProvider.get_features`

- **Type**: method
- **Module**: `osm_features.provider`
- **Class**: `OSMOverpassProvider`
- **Signature**: `get_features(self, latitude: float, longitude: float, radius_m: int, timeout_s: int) -> OSMFetchResult`
- **Description**: Get geographic features around a location.

### `OSMOverpassProvider.is_available`

- **Type**: method
- **Module**: `osm_features.provider`
- **Class**: `OSMOverpassProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if Overpass API is available.

### `OSMReverseGeocodingProvider.__init__`

- **Type**: method
- **Module**: `reverse_geocoding.providers.osm`
- **Class**: `OSMReverseGeocodingProvider`
- **Signature**: `__init__(self, endpoint: str, user_agent: str) -> None`
- **Description**: Initialize OSM Nominatim reverse geocoding provider.

### `OSMReverseGeocodingProvider.fetch`

- **Type**: method
- **Module**: `reverse_geocoding.providers.osm`
- **Class**: `OSMReverseGeocodingProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> ReverseGeocodeFetchResult`
- **Description**: Fetch reverse geocoding data from OSM Nominatim API.

## P

### `parse_args`

- **Type**: function
- **Module**: `schema_inference`
- **Signature**: `parse_args() -> argparse.Namespace`

### `parse_args`

- **Type**: function
- **Module**: `schema_statistics`
- **Signature**: `parse_args() -> argparse.Namespace`

### `process_biosamples`

- **Type**: function
- **Module**: `elevation_demos`
- **Signature**: `process_biosamples(input_file: Path, output_file: Path, timeout: float, no_cache: bool, providers: tuple[str, ...], output_format: str) -> None`
- **Description**: Process elevation lookups for synthetic biosamples JSON file.

### `providers`

- **Type**: function
- **Module**: `cli_soil`
- **Signature**: `providers(verbose: bool) -> None`
- **Description**: Show status of soil data providers.

### `providers`

- **Type**: function
- **Module**: `cli_land`
- **Signature**: `providers()`
- **Description**: Show status of all land cover and vegetation providers.

### `providers`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `providers()`
- **Description**: Show status of all forward geocoding providers.

### `providers`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `providers()`
- **Description**: Show status of OSM features providers.

### `providers`

- **Type**: function
- **Module**: `cli_marine`
- **Signature**: `providers()`
- **Description**: List available marine data providers and their capabilities.

## R

### `RateLimiter.__init__`

- **Type**: method
- **Module**: `elevation.location_detector`
- **Class**: `RateLimiter`
- **Signature**: `__init__(self) -> None`

### `RateLimiter.wait_if_needed`

- **Type**: method
- **Module**: `elevation.location_detector`
- **Class**: `RateLimiter`
- **Signature**: `wait_if_needed(self, service: str, min_interval: float) -> None`
- **Description**: Ensure minimum interval between requests for a service.

### `request`

- **Type**: function
- **Module**: `http_cache`
- **Signature**: `request(method: str, url: str, read_from_cache: bool, write_to_cache: bool) -> requests.Response`
- **Description**: Make cached HTTP request with coordinate canonicalization.

### `reset_session`

- **Type**: function
- **Module**: `http_cache`
- **Signature**: `reset_session()`
- **Description**: Close and clear the module session (for tests).

### `ReverseGeocodeResult.filter_by_type`

- **Type**: method
- **Module**: `reverse_geocoding_models`
- **Class**: `ReverseGeocodeResult`
- **Signature**: `filter_by_type(self, place_type: PlaceType) -> list[ReverseGeocodeLocation]`
- **Description**: Filter locations by place type.

### `ReverseGeocodeResult.get_best_match`

- **Type**: method
- **Module**: `reverse_geocoding_models`
- **Class**: `ReverseGeocodeResult`
- **Signature**: `get_best_match(self) -> ReverseGeocodeLocation | None`
- **Description**: Get the best matching location (first in list).

### `ReverseGeocodeResult.get_country`

- **Type**: method
- **Module**: `reverse_geocoding_models`
- **Class**: `ReverseGeocodeResult`
- **Signature**: `get_country(self) -> str | None`
- **Description**: Get country from the best match.

### `ReverseGeocodeResult.get_formatted_address`

- **Type**: method
- **Module**: `reverse_geocoding_models`
- **Class**: `ReverseGeocodeResult`
- **Signature**: `get_formatted_address(self) -> str | None`
- **Description**: Get formatted address from the best match.

### `ReverseGeocodeResult.to_simple_dict`

- **Type**: method
- **Module**: `reverse_geocoding_models`
- **Class**: `ReverseGeocodeResult`
- **Signature**: `to_simple_dict(self) -> dict[str, Any]`
- **Description**: Convert to simple dictionary for easy viewing.

### `ReverseGeocodingProvider.choices`

- **Type**: method
- **Module**: `providers`
- **Class**: `ReverseGeocodingProvider`
- **Signature**: `choices(cls) -> list[str]`
- **Description**: Get list of provider choices for Click.

### `ReverseGeocodingProvider.description`

- **Type**: method
- **Module**: `providers`
- **Class**: `ReverseGeocodingProvider`
- **Signature**: `description(cls) -> str`
- **Description**: Get formatted description of all available providers.

### `ReverseGeocodingProvider.fetch`

- **Type**: method
- **Module**: `reverse_geocoding.providers.base`
- **Class**: `ReverseGeocodingProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> ReverseGeocodeFetchResult`
- **Description**: Fetch reverse geocoding data for the given coordinates.

### `ReverseGeocodingProvider.info`

- **Type**: method
- **Module**: `providers`
- **Class**: `ReverseGeocodingProvider`
- **Signature**: `info(cls, provider: 'ReverseGeocodingProvider | str') -> ProviderInfo`
- **Description**: Get detailed information about a provider.

### `ReverseGeocodingService.__init__`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `__init__(self) -> None`
- **Description**: Initialize the reverse geocoding service.

### `ReverseGeocodingService.compare_providers`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `compare_providers(self, lat: float, lon: float) -> dict[str, Any]`
- **Description**: Compare results from all available providers.

### `ReverseGeocodingService.get_available_providers`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `get_available_providers(self) -> list[str]`
- **Description**: Get list of available provider names.

### `ReverseGeocodingService.get_provider`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `get_provider(self, name: str) -> ReverseGeocodingProvider | None`
- **Description**: Get a specific provider by name.

### `ReverseGeocodingService.reverse_geocode`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `reverse_geocode(self, lat: float, lon: float, provider: str | None) -> ReverseGeocodeResult | None`
- **Description**: Perform reverse geocoding using specified or default provider.

### `ReverseGeocodingService.reverse_geocode_multiple`

- **Type**: method
- **Module**: `reverse_geocoding.service`
- **Class**: `ReverseGeocodingService`
- **Signature**: `reverse_geocode_multiple(self, lat: float, lon: float, providers: list[str] | None) -> dict[str, ReverseGeocodeResult]`
- **Description**: Perform reverse geocoding using multiple providers sequentially.

## S

### `set_session_for_tests`

- **Type**: function
- **Module**: `http_cache`
- **Signature**: `set_session_for_tests(session: CachedSession)`
- **Description**: Force http_cache.get_session() to return a provided session (for tests).

### `setup_logging`

- **Type**: function
- **Module**: `logging_config`
- **Signature**: `setup_logging(level: str, log_file: str | None, enable_file_logging: bool) -> logging.Logger`
- **Description**: Set up centralized logging with console and optional file output.

### `show_mapping_info`

- **Type**: function
- **Module**: `cli_biosample_elevation`
- **Signature**: `show_mapping_info() -> None`
- **Description**: Display comprehensive field mapping information and examples.

### `show_version`

- **Type**: function
- **Module**: `cli`
- **Signature**: `show_version() -> None`
- **Description**: Print the biosample-enricher version.

### `SmartOpenTopoDataProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.open_topo_data`
- **Class**: `SmartOpenTopoDataProvider`
- **Signature**: `__init__(self, endpoint: str) -> None`
- **Description**: Initialize smart provider with automatic dataset selection.

### `SmartOpenTopoDataProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.open_topo_data`
- **Class**: `SmartOpenTopoDataProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation using optimal dataset for location.

### `soil`

- **Type**: function
- **Module**: `cli_soil`
- **Signature**: `soil() -> None`
- **Description**: Soil enrichment commands for biosample site characterization.

### `SoilGridsProvider.__init__`

- **Type**: method
- **Module**: `soil.providers.soilgrids`
- **Class**: `SoilGridsProvider`
- **Signature**: `__init__(self, timeout: int)`

### `SoilGridsProvider.coverage_description`

- **Type**: method
- **Module**: `soil.providers.soilgrids`
- **Class**: `SoilGridsProvider`
- **Signature**: `coverage_description(self) -> str`

### `SoilGridsProvider.get_soil_data`

- **Type**: method
- **Module**: `soil.providers.soilgrids`
- **Class**: `SoilGridsProvider`
- **Signature**: `get_soil_data(self, latitude: float, longitude: float, depth_cm: str | None) -> SoilResult`
- **Description**: Get SoilGrids soil data for a location.

### `SoilGridsProvider.is_available`

- **Type**: method
- **Module**: `soil.providers.soilgrids`
- **Class**: `SoilGridsProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if SoilGrids services are available.

### `SoilGridsProvider.name`

- **Type**: method
- **Module**: `soil.providers.soilgrids`
- **Class**: `SoilGridsProvider`
- **Signature**: `name(self) -> str`

### `SoilObservation.validate_texture_class`

- **Type**: method
- **Module**: `soil.models`
- **Class**: `SoilObservation`
- **Signature**: `validate_texture_class(cls, v: str | None) -> str | None`
- **Description**: Validate USDA texture class names.

### `SoilProviderBase.calculate_quality_score`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `calculate_quality_score(self, distance_m: float | None, confidence: float | None, data_completeness: float) -> float`
- **Description**: Calculate overall data quality score.

### `SoilProviderBase.coverage_description`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `coverage_description(self) -> str`
- **Description**: Description of geographic and data coverage.

### `SoilProviderBase.get_soil_data`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `get_soil_data(self, latitude: float, longitude: float, depth_cm: str | None) -> SoilResult`
- **Description**: Retrieve soil data for a specific location.

### `SoilProviderBase.is_available`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if the provider is currently available.

### `SoilProviderBase.name`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `name(self) -> str`
- **Description**: Provider name for identification and logging.

### `SoilProviderBase.validate_coordinates`

- **Type**: method
- **Module**: `soil.providers.base`
- **Class**: `SoilProviderBase`
- **Signature**: `validate_coordinates(self, latitude: float, longitude: float) -> None`
- **Description**: Validate coordinate inputs.

### `SoilResult.to_gold_schema`

- **Type**: method
- **Module**: `soil.models`
- **Class**: `SoilResult`
- **Signature**: `to_gold_schema(self) -> dict[str, Any]`
- **Description**: Convert to GOLD biosample schema format.

### `SoilResult.to_nmdc_schema`

- **Type**: method
- **Module**: `soil.models`
- **Class**: `SoilResult`
- **Signature**: `to_nmdc_schema(self) -> dict[str, Any]`
- **Description**: Convert to NMDC biosample schema format.

### `SoilService.__init__`

- **Type**: method
- **Module**: `soil.service`
- **Class**: `SoilService`
- **Signature**: `__init__(self)`
- **Description**: Initialize soil service with providers.

### `SoilService.enrich_batch`

- **Type**: method
- **Module**: `soil.service`
- **Class**: `SoilService`
- **Signature**: `enrich_batch(self, locations: list[tuple[float, float]], depth_cm: str | None) -> list[SoilResult]`
- **Description**: Enrich multiple locations with soil data.

### `SoilService.enrich_biosample`

- **Type**: method
- **Module**: `soil.service`
- **Class**: `SoilService`
- **Signature**: `enrich_biosample(self, sample_data: dict) -> dict`
- **Description**: Enrich a single biosample with soil data.

### `SoilService.enrich_location`

- **Type**: method
- **Module**: `soil.service`
- **Class**: `SoilService`
- **Signature**: `enrich_location(self, latitude: float, longitude: float, depth_cm: str | None) -> SoilResult`
- **Description**: Enrich a single location with soil data.

### `SoilService.get_provider_status`

- **Type**: method
- **Module**: `soil.service`
- **Class**: `SoilService`
- **Signature**: `get_provider_status(self) -> dict[str, dict]`
- **Description**: Get status of all soil providers.

## T

### `test`

- **Type**: function
- **Module**: `cli_soil`
- **Signature**: `test(latitude: float, longitude: float, provider: str, depth: str, verbose: bool) -> None`
- **Description**: Test soil data providers at a specific location.

### `test`

- **Type**: function
- **Module**: `cache_management`
- **Signature**: `test(ctx: click.Context, url: str, method: str, params: str | None) -> None`
- **Description**: Test cache functionality with a request.

### `test`

- **Type**: function
- **Module**: `cli_land`
- **Signature**: `test(lat: float, lon: float, date: datetime | None)`
- **Description**: Test land enrichment with sample coordinates.

### `test`

- **Type**: function
- **Module**: `cli_forward_geocoding`
- **Signature**: `test(query: str)`
- **Description**: Test forward geocoding with a sample place name.

### `test`

- **Type**: function
- **Module**: `cli_osm_features`
- **Signature**: `test(latitude: float, longitude: float, radius: int)`
- **Description**: Test OSM features enrichment with sample coordinates.

### `test`

- **Type**: function
- **Module**: `cli_marine`
- **Signature**: `test(lat: float, lon: float, date: str)`
- **Description**: Test marine data providers for a specific location and date.

### `test_connection`

- **Type**: function
- **Module**: `cli_metrics`
- **Signature**: `test_connection(nmdc_connection: str | None, gold_connection: str | None) -> None`
- **Description**: Test database connections.

### `typeof`

- **Type**: function
- **Module**: `schema_statistics`
- **Signature**: `typeof(v: Any) -> str`

## U

### `UnifiedBiosampleFetcher.__init__`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `__init__(self) -> None`

### `UnifiedBiosampleFetcher.configure_gold_mongo`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `configure_gold_mongo(self, connection_string: str, database: str, collection: str) -> None`
- **Description**: Configure GOLD MongoDB connection.

### `UnifiedBiosampleFetcher.configure_nmdc_mongo`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `configure_nmdc_mongo(self, connection_string: str, database: str, collection: str) -> None`
- **Description**: Configure NMDC MongoDB connection.

### `UnifiedBiosampleFetcher.fetch_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `fetch_enrichable_locations(self, source: str, limit: int | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch enrichable locations from configured sources.

### `UnifiedBiosampleFetcher.fetch_locations_by_ids`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `fetch_locations_by_ids(self, ids: list[str], source: str, id_field: str | None) -> Iterator[BiosampleLocation]`
- **Description**: Fetch locations by IDs from configured sources.

### `UnifiedBiosampleFetcher.fetch_random_enrichable_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `fetch_random_enrichable_locations(self, n: int, source: str) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random enrichable locations from configured sources.

### `UnifiedBiosampleFetcher.fetch_random_locations`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `fetch_random_locations(self, n: int, source: str) -> Iterator[BiosampleLocation]`
- **Description**: Fetch N random locations from configured sources.

### `UnifiedBiosampleFetcher.get_enrichment_statistics`

- **Type**: method
- **Module**: `adapters`
- **Class**: `UnifiedBiosampleFetcher`
- **Signature**: `get_enrichment_statistics(self) -> dict[str, Any]`
- **Description**: Get statistics about available enrichable samples.

### `USDANRCSProvider.__init__`

- **Type**: method
- **Module**: `soil.providers.usda_nrcs`
- **Class**: `USDANRCSProvider`
- **Signature**: `__init__(self, timeout: int)`

### `USDANRCSProvider.coverage_description`

- **Type**: method
- **Module**: `soil.providers.usda_nrcs`
- **Class**: `USDANRCSProvider`
- **Signature**: `coverage_description(self) -> str`

### `USDANRCSProvider.get_soil_data`

- **Type**: method
- **Module**: `soil.providers.usda_nrcs`
- **Class**: `USDANRCSProvider`
- **Signature**: `get_soil_data(self, latitude: float, longitude: float, depth_cm: str | None) -> SoilResult`
- **Description**: Get USDA soil taxonomy data for a location.

### `USDANRCSProvider.is_available`

- **Type**: method
- **Module**: `soil.providers.usda_nrcs`
- **Class**: `USDANRCSProvider`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if USDA SDA is available.

### `USDANRCSProvider.name`

- **Type**: method
- **Module**: `soil.providers.usda_nrcs`
- **Class**: `USDANRCSProvider`
- **Signature**: `name(self) -> str`

### `USGSElevationProvider.__init__`

- **Type**: method
- **Module**: `elevation.providers.usgs`
- **Class**: `USGSElevationProvider`
- **Signature**: `__init__(self) -> None`
- **Description**: Initialize USGS Elevation provider.

### `USGSElevationProvider.fetch`

- **Type**: method
- **Module**: `elevation.providers.usgs`
- **Class**: `USGSElevationProvider`
- **Signature**: `fetch(self, lat: float, lon: float) -> FetchResult`
- **Description**: Fetch elevation data from USGS 3DEP ArcGIS service.

## V

### `validate_elevation_providers`

- **Type**: function
- **Module**: `providers`
- **Signature**: `validate_elevation_providers(providers_str: str | None) -> list[str] | None`
- **Description**: Validate and parse elevation provider string.

### `validate_geocoding_providers`

- **Type**: function
- **Module**: `providers`
- **Signature**: `validate_geocoding_providers(providers_str: str | None) -> list[str] | None`
- **Description**: Validate and parse reverse geocoding provider string.

### `VegetationObservation.validate_location`

- **Type**: method
- **Module**: `land.models`
- **Class**: `VegetationObservation`
- **Signature**: `validate_location(cls, v: dict[str, float]) -> dict[str, float]`
- **Description**: Validate location coordinates.

### `VegetationProviderBase.calculate_spatial_distance`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `calculate_spatial_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float`
- **Description**: Calculate distance between two points using Haversine formula.

### `VegetationProviderBase.calculate_temporal_offset`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `calculate_temporal_offset(self, target_date: date, actual_date: date) -> int`
- **Description**: Calculate temporal offset between target and actual dates.

### `VegetationProviderBase.coverage_description`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `coverage_description(self) -> str`
- **Description**: Description of geographic and temporal coverage.

### `VegetationProviderBase.get_vegetation_indices`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `get_vegetation_indices(self, latitude: float, longitude: float, target_date: date | None, time_window_days: int) -> list[VegetationObservation]`
- **Description**: Retrieve vegetation indices for a specific location and date.

### `VegetationProviderBase.is_available`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `is_available(self) -> bool`
- **Description**: Check if the provider is currently available.

### `VegetationProviderBase.name`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `name(self) -> str`
- **Description**: Provider name for identification and logging.

### `VegetationProviderBase.validate_coordinates`

- **Type**: method
- **Module**: `land.providers.base`
- **Class**: `VegetationProviderBase`
- **Signature**: `validate_coordinates(self, latitude: float, longitude: float) -> None`
- **Description**: Validate coordinate inputs.

### `visualize`

- **Type**: function
- **Module**: `cli_metrics`
- **Signature**: `visualize(csv_file: Path, output_dir: Path) -> None`
- **Description**: Create visualizations from existing metrics CSV file.

## W

### `walk`

- **Type**: function
- **Module**: `schema_statistics`
- **Signature**: `walk(doc: Any, prefix: str, seen: dict[str, dict], max_examples: int, doc_id: str) -> None`
- **Description**: Recursively record stats for each path.

### `weather_cli`

- **Type**: function
- **Module**: `cli_weather`
- **Signature**: `weather_cli(debug: bool)`
- **Description**: Weather enrichment CLI for biosample environmental context.

### `WeatherEnrichmentMetrics.__init__`

- **Type**: method
- **Module**: `weather.metrics`
- **Class**: `WeatherEnrichmentMetrics`
- **Signature**: `__init__(self)`

### `WeatherEnrichmentMetrics.analyze_biosample_collection`

- **Type**: method
- **Module**: `weather.metrics`
- **Class**: `WeatherEnrichmentMetrics`
- **Signature**: `analyze_biosample_collection(self, biosamples: list[dict[str, Any]], source: str) -> dict[str, Any]`
- **Description**: Analyze weather field coverage before and after enrichment for a collection of biosamples.

### `WeatherEnrichmentMetrics.export_detailed_results`

- **Type**: method
- **Module**: `weather.metrics`
- **Class**: `WeatherEnrichmentMetrics`
- **Signature**: `export_detailed_results(self, output_path: str) -> None`
- **Description**: Export detailed enrichment results to CSV for further analysis.

### `WeatherEnrichmentMetrics.generate_metrics_report`

- **Type**: method
- **Module**: `weather.metrics`
- **Class**: `WeatherEnrichmentMetrics`
- **Signature**: `generate_metrics_report(self, analyses: list[dict[str, Any]]) -> pd.DataFrame`
- **Description**: Generate comprehensive metrics report in tabular format.

### `WeatherObservation.validate_value`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `WeatherObservation`
- **Signature**: `validate_value(cls, v)`
- **Description**: Validate that value is either a number or dict with numeric values.

### `WeatherProviderBase.__init__`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `__init__(self, timeout: int)`

### `WeatherProviderBase.get_coverage_period`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_coverage_period(self) -> dict[str, str]`
- **Description**: Return temporal coverage period.

### `WeatherProviderBase.get_daily_weather`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_daily_weather(self, lat: float, lon: float, target_date: date, parameters: list | None) -> WeatherResult`
- **Description**: Get weather data for a specific date and location.

### `WeatherProviderBase.get_provider_info`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_provider_info(self) -> dict[str, Any]`
- **Description**: Get provider metadata and capabilities.

### `WeatherProviderBase.get_spatial_resolution`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_spatial_resolution(self) -> str`
- **Description**: Return spatial resolution (e.g., '11km', 'station-based').

### `WeatherProviderBase.get_supported_parameters`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_supported_parameters(self) -> list`
- **Description**: Return list of weather parameters this provider supports.

### `WeatherProviderBase.get_temporal_resolution`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `get_temporal_resolution(self) -> str`
- **Description**: Return temporal resolution (e.g., 'hourly', 'daily').

### `WeatherProviderBase.is_available`

- **Type**: method
- **Module**: `weather.providers.base`
- **Class**: `WeatherProviderBase`
- **Signature**: `is_available(self, lat: float, lon: float, target_date: date) -> bool`
- **Description**: Check if provider has data available for given location and date.

### `WeatherResult.get_coverage_metrics`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `WeatherResult`
- **Signature**: `get_coverage_metrics(self) -> dict[str, Any]`
- **Description**: Generate before/after coverage metrics for this weather enrichment.

### `WeatherResult.get_schema_mapping`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `WeatherResult`
- **Signature**: `get_schema_mapping(self, target_schema: str) -> dict[str, Any]`
- **Description**: Map weather observations to target biosample schema fields.

### `WeatherResult.validate_date_format`

- **Type**: method
- **Module**: `weather.models`
- **Class**: `WeatherResult`
- **Signature**: `validate_date_format(cls, v)`
- **Description**: Ensure collection date is in YYYY-MM-DD format.

### `WeatherService.__init__`

- **Type**: method
- **Module**: `weather.service`
- **Class**: `WeatherService`
- **Signature**: `__init__(self, providers: list[WeatherProviderBase] | None)`
- **Description**: Initialize weather service with provider chain.

### `WeatherService.get_climate_normals`

- **Type**: method
- **Module**: `weather.service`
- **Class**: `WeatherService`
- **Signature**: `get_climate_normals(self, lat: float, lon: float, years_back: int, providers: list[str] | None) -> MultiProviderClimateNormals`
- **Description**: Get climate averages (normals) for a location from all available providers.

### `WeatherService.get_daily_weather`

- **Type**: method
- **Module**: `weather.service`
- **Class**: `WeatherService`
- **Signature**: `get_daily_weather(self, lat: float, lon: float, target_date: date, parameters: list[str] | None) -> WeatherResult`
- **Description**: Get daily weather data by integrating results from all providers.

### `WeatherService.get_provider_info`

- **Type**: method
- **Module**: `weather.service`
- **Class**: `WeatherService`
- **Signature**: `get_provider_info(self) -> list[dict[str, Any]]`
- **Description**: Get information about all configured providers.

### `WeatherService.get_weather_for_biosample`

- **Type**: method
- **Module**: `weather.service`
- **Class**: `WeatherService`
- **Signature**: `get_weather_for_biosample(self, biosample: dict[str, Any], target_schema: str) -> dict[str, Any]`
- **Description**: Get weather data for a biosample and map to target schema.

---

*This index was automatically generated by `scripts/generate_api_index.py`*
