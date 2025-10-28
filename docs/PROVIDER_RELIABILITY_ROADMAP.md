# Provider Reliability Roadmap

**Objective:** Fix critical reliability gaps and stabilize all data fetching providers

---

## Priority 1: Critical Issues (Must Fix)

### 1.1 USGS Elevation Service Unreliability

**Current Status:** Marked as `@pytest.mark.flaky` in tests, documented migration issues

**Action Items:**
```python
# File: biosample_enricher/elevation/providers/usgs.py

# 1. Add comprehensive retry logic with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
def fetch(self, lat, lon, **kwargs):
    # Existing fetch implementation
    pass

# 2. Add service health check
def _check_service_health(self) -> bool:
    try:
        # Test query at a known location (e.g., Mt. Everest)
        test_result = self.fetch(27.9881, 86.9250, timeout_s=5)
        return test_result.ok
    except Exception:
        return False

# 3. Add fallback provider recommendation
def fetch(self, lat, lon, **kwargs):
    if not self._check_service_health():
        logger.warning(
            "USGS 3DEP service unhealthy. "
            "Recommend using Open Topo Data as fallback."
        )
        raise ServiceUnavailableError(
            "USGS 3DEP service unavailable. "
            "Use fallback provider (Open Topo Data)"
        )
    # ... rest of implementation
```

**Timeline:** 1 week
**Owner:** Primary elevation provider team

**Success Criteria:**
- [ ] Health check passes in local testing
- [ ] Retry logic reduces flakiness
- [ ] Test passes consistently without `@pytest.mark.flaky`

---

### 1.2 Marine Providers: GEBCO WCS Implementation

**Current Status:** Placeholder depth estimation, no actual WCS queries

**Action Items:**
```python
# File: biosample_enricher/marine/providers/gebco.py

# Replace fallback estimation with real WCS client
from owslib.wcs import WebCoverageService

class GEBCOProvider(MarineProviderBase):
    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        # GEBCO WCS 2.0.1 endpoint
        self.wcs_url = "https://www.gebco.net/data_and_products/gebco_web_services/web_map_service"
        self._wcs_client = None

    def _get_wcs_client(self) -> WebCoverageService:
        if self._wcs_client is None:
            self._wcs_client = WebCoverageService(
                self.wcs_url,
                version='2.0.1'
            )
        return self._wcs_client

    def _fetch_bathymetry_data(self, latitude, longitude) -> float | None:
        """Fetch actual GEBCO bathymetry via WCS."""
        try:
            wcs = self._get_wcs_client()

            # Query GEBCO_2023 coverage
            coverage = 'GEBCO_2023'

            # Small area around point
            bbox = (
                longitude - 0.01,
                latitude - 0.01,
                longitude + 0.01,
                latitude + 0.01
            )

            # GetCoverage request for GeoTIFF
            response = wcs.getCoverage(
                identifier=coverage,
                BoundingBox=bbox,
                format='image/tiff',
                CRS='EPSG:4326'
            )

            # Parse GeoTIFF and extract value at point
            from rasterio.io import MemoryFile
            with MemoryFile(response.read()) as mem:
                with mem.open() as src:
                    # Get value at coordinates
                    row, col = src.index(longitude, latitude)
                    value = src.read(1)[int(row), int(col)]

                    # Handle no-data values
                    if value == src.nodata or np.isnan(value):
                        return None

                    return float(value)

        except Exception as e:
            logger.error(f"GEBCO WCS fetch failed: {e}")
            return None
```

**Dependencies:**
```bash
uv add owslib rasterio
```

**Timeline:** 1.5 weeks
**Owner:** Marine data team

**Success Criteria:**
- [ ] Real WCS queries return actual bathymetry data
- [ ] Handle no-data values properly
- [ ] Values in expected range (-11000m to +8000m)
- [ ] Test passes with actual GEBCO data

---

### 1.3 Marine Providers: ERDDAP Integration

**Current Status:** Simplified ERDDAP queries, no actual data retrieval

**Action Items:**
```python
# File: biosample_enricher/marine/providers/esa_cci.py

import xarray as xr
import requests

class ESACCIProvider(MarineProviderBase):
    def __init__(self, timeout: int = 30):
        super().__init__(timeout)
        self.erddap_url = "https://coastwatch.pfeg.noaa.gov/erddap"
        self.dataset_id = "noaa_esrl_ocean_color_v2"  # Actual ESA CCI dataset

    def _fetch_chlorophyll_data(self, latitude, longitude, target_date) -> float | None:
        """Fetch actual chlorophyll-a data from ERDDAP."""
        try:
            date_str = target_date.strftime("%Y-%m-%d")

            # Build proper ERDDAP griddap query
            url = (
                f"{self.erddap_url}/griddap/{self.dataset_id}.nc?"
                f"chlor_a[({date_str}T00:00:00Z):1:({date_str}T23:59:59Z)]"
                f"[({latitude}):1:({latitude})]"
                f"[({longitude}):1:({longitude})]"
            )

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse NetCDF response
            with xr.open_dataset(io.BytesIO(response.content)) as ds:
                # Extract chlorophyll value
                if 'chlor_a' in ds.data_vars:
                    chl_value = ds['chlor_a'].values.flatten()[0]

                    # Validate range and no-data values
                    if np.isnan(chl_value) or chl_value < 0:
                        return None

                    if not 0.001 <= chl_value <= 100:
                        logger.warning(f"Value outside expected range: {chl_value}")
                        return None

                    return float(chl_value)

            return None

        except requests.exceptions.Timeout:
            logger.error(f"ERDDAP timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"ERDDAP fetch failed: {e}")
            return None
```

**Dependencies:**
```bash
uv add xarray netCDF4
```

**Timeline:** 1.5 weeks
**Owner:** Marine data team

**Success Criteria:**
- [ ] Real ERDDAP griddap queries return data
- [ ] Proper NetCDF parsing
- [ ] Values in expected range (0.001-100 mg/m³)
- [ ] Handles missing data gracefully

---

### 1.4 NOAA OISST Integration

**Current Status:** Placeholder queries, no real data retrieval

**Action Items:**
```python
# File: biosample_enricher/marine/providers/noaa_oisst.py

import xarray as xr

class NOAAOISSTProvider(MarineProviderBase):
    def _fetch_sst_data(self, latitude, longitude, target_date) -> float | None:
        """Fetch actual SST from NOAA OISST ERDDAP."""
        try:
            # Convert to 0-360 longitude
            lon_360 = longitude if longitude >= 0 else longitude + 360
            date_str = target_date.strftime("%Y-%m-%d")

            # Build proper ERDDAP griddap query for OISST
            # Dataset: https://coastwatch.pfeg.noaa.gov/erddap/info/ncdcOisst2Agg/index.html
            url = (
                f"{self.base_url}/ncdcOisst2Agg.nc?"
                f"sst[({date_str}):1:({date_str})]"
                f"[(0.0):1:(0.0)]"  # Surface level
                f"[({latitude}):1:({latitude})]"
                f"[({lon_360}):1:({lon_360})]"
            )

            response = request("GET", url, timeout=self.timeout)
            response.raise_for_status()

            # Parse NetCDF
            with xr.open_dataset(io.BytesIO(response.content)) as ds:
                if 'sst' in ds.data_vars:
                    sst_value = ds['sst'].values.flatten()[0]

                    # Check for no-data and range
                    if np.isnan(sst_value):
                        return None

                    if not -5.0 <= sst_value <= 50.0:
                        logger.warning(f"SST outside range: {sst_value}°C")
                        return None

                    return float(sst_value)

            return None

        except Exception as e:
            logger.error(f"OISST fetch failed: {e}")
            return None
```

**Timeline:** 1.5 weeks
**Owner:** Marine data team

**Success Criteria:**
- [ ] Real ERDDAP queries return SST data
- [ ] Values in expected range (-5 to 50°C)
- [ ] Proper no-data handling

---

### 1.5 MODIS Vegetation: Full APPEEARS Integration

**Current Status:** Mock data generation, no real APPEEARS API

**Action Items:**
```python
# File: biosample_enricher/land/providers/modis_vegetation.py

import requests
import json
from datetime import datetime, timedelta

class MODISVegetationProvider(VegetationProviderBase):
    def __init__(self, username: str = None, password: str = None, timeout: int = 60):
        self.appeears_base = "https://appeears.earthdatacloud.nasa.gov/api/v1"
        self.timeout = timeout
        self.username = username or os.getenv("NASA_USERNAME")
        self.password = password or os.getenv("NASA_PASSWORD")
        self._session = get_session()
        self._token = None

        if not self.username or not self.password:
            raise ValueError(
                "NASA Earth Data credentials required. "
                "Set NASA_USERNAME and NASA_PASSWORD environment variables."
            )

    def _authenticate(self) -> str:
        """Get APPEEARS API token."""
        if self._token:
            return self._token

        try:
            response = self._session.post(
                f"{self.appeears_base}/login",
                json={"username": self.username, "password": self.password},
                timeout=5
            )
            response.raise_for_status()
            self._token = response.json()['token']
            return self._token
        except Exception as e:
            raise ValueError(f"APPEEARS authentication failed: {e}")

    def _query_modis_product(
        self,
        latitude: float,
        longitude: float,
        target_date: date,
        time_window_days: int,
        product_name: str,
        product_info: dict,
    ) -> VegetationObservation | None:
        """Query actual MODIS data via APPEEARS."""
        try:
            token = self._authenticate()
            headers = {"Authorization": f"Bearer {token}"}

            # Build date range
            start_date = target_date - timedelta(days=time_window_days // 2)
            end_date = target_date + timedelta(days=time_window_days // 2)

            # APPEEARS task request
            task = {
                "task_type": "point",
                "params": {
                    "coordinates": [{"latitude": latitude, "longitude": longitude}],
                    "products": [
                        {
                            "product": product_name,
                            "layer": product_info["layers"][0]
                        }
                    ],
                    "dates": [
                        {
                            "startDate": start_date.isoformat(),
                            "endDate": end_date.isoformat()
                        }
                    ]
                }
            }

            # Submit task
            response = self._session.post(
                f"{self.appeears_base}/task",
                json=task,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            task_id = response.json()['task_id']

            # Poll for completion
            max_wait = 300  # 5 minutes
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < max_wait:
                status_resp = self._session.get(
                    f"{self.appeears_base}/task/{task_id}",
                    headers=headers,
                    timeout=self.timeout
                )
                status_resp.raise_for_status()
                status = status_resp.json()['status']

                if status == 'completed':
                    # Get results
                    results_resp = self._session.get(
                        f"{self.appeears_base}/task/{task_id}/result",
                        headers=headers,
                        timeout=self.timeout
                    )
                    results_resp.raise_for_status()
                    results = results_resp.json()['data']

                    # Parse results
                    return self._parse_appeears_results(
                        results, latitude, longitude, target_date, product_info
                    )

                elif status in ['failed', 'cancelled']:
                    raise ValueError(f"APPEEARS task {status}")

                time.sleep(10)  # Wait 10 seconds before next poll

            raise TimeoutError(f"APPEEARS task timeout after {max_wait}s")

        except Exception as e:
            logger.error(f"MODIS APPEEARS query failed: {e}")
            return None

    def _parse_appeears_results(
        self, results, latitude, longitude, target_date, product_info
    ) -> VegetationObservation | None:
        """Parse APPEEARS result into observation."""
        # Implementation depends on APPEEARS response format
        # Typically returns array of values with dates
        pass
```

**Requirements:**
- NASA Earth Data account setup
- APPEEARS API credentials
- Environment variables: NASA_USERNAME, NASA_PASSWORD

**Timeline:** 2 weeks
**Owner:** Land data team

**Success Criteria:**
- [ ] Real APPEEARS task submission and polling
- [ ] Proper authentication and token handling
- [ ] Results parsing and validation
- [ ] NDVI/EVI/LAI/FPAR extraction

---

## Priority 2: Important Enhancements (Should Fix)

### 2.1 Implement Circuit Breaker Pattern

**File:** `biosample_enricher/providers/circuit_breaker.py`

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Provider failed, blocking calls
    HALF_OPEN = "half_open"  # Testing if provider recovered

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(
                    f"Circuit open. Retry after {self._time_until_retry()}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit closed - service recovered")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit opened - service failed {self.failure_count} times"
            )

    def _should_attempt_reset(self) -> bool:
        return (
            datetime.now() - self.last_failure_time
            > timedelta(seconds=self.recovery_timeout)
        )

    def _time_until_retry(self) -> int:
        elapsed = (datetime.now() - self.last_failure_time).seconds
        return max(0, self.recovery_timeout - elapsed)
```

**Integration:**
```python
# In elevation provider
from biosample_enricher.providers.circuit_breaker import CircuitBreaker

class GoogleElevationProvider:
    def __init__(self, api_key):
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    def fetch(self, lat, lon, **kwargs):
        return self.circuit_breaker.call(
            self._fetch_impl, lat, lon, **kwargs
        )
```

**Timeline:** 1 week
**Owner:** Infrastructure team

---

### 2.2 Implement Exponential Backoff Retry Logic

**File:** `biosample_enricher/providers/retry_logic.py`

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    retry_if_exception_type,
    before_log,
    after_log
)

RETRY_CONFIG = {
    "elevation": {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=1, max=10),
        "retry": retry_if_exception_type(
            (TimeoutError, ConnectionError, requests.RequestException)
        ),
    },
    "soil": {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=2, max=30),
        "retry": retry_if_exception_type(
            (TimeoutError, ConnectionError, requests.RequestException)
        ),
    },
    "marine": {
        "stop": stop_after_attempt(5),
        "wait": wait_exponential(multiplier=2, min=2, max=60) + wait_random(0, 5),
        "retry": retry_if_exception_type(Exception),
    },
}

def create_retry_decorator(service: str):
    config = RETRY_CONFIG.get(service, RETRY_CONFIG["elevation"])

    return retry(
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
        **config
    )
```

**Timeline:** 1 week
**Owner:** Infrastructure team

---

### 2.3 Add Provider Health Checks

**File:** `biosample_enricher/providers/health_check.py`

```python
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timedelta

@dataclass
class HealthStatus:
    provider: str
    healthy: bool
    last_check: datetime
    error: Optional[str] = None
    response_time_ms: Optional[float] = None

    def age_seconds(self) -> float:
        return (datetime.now() - self.last_check).total_seconds()

class ProviderHealthChecker:
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl = cache_ttl_seconds
        self.health_cache: Dict[str, HealthStatus] = {}

    def check_provider(self, provider_name: str) -> HealthStatus:
        """Check provider health with caching."""

        # Check cache
        if provider_name in self.health_cache:
            cached = self.health_cache[provider_name]
            if cached.age_seconds() < self.cache_ttl:
                return cached

        # Perform health check
        status = self._perform_health_check(provider_name)
        self.health_cache[provider_name] = status

        return status

    def _perform_health_check(self, provider_name: str) -> HealthStatus:
        """Implement health check for each provider."""

        health_checks = {
            "google_elevation": self._check_google_elevation,
            "usgs_3dep": self._check_usgs_elevation,
            "open_topo_data": self._check_open_topo_data,
            "osm_elevation": self._check_osm_elevation,
            # ... etc
        }

        check_func = health_checks.get(provider_name)
        if not check_func:
            return HealthStatus(
                provider=provider_name,
                healthy=False,
                last_check=datetime.now(),
                error="Unknown provider"
            )

        try:
            return check_func()
        except Exception as e:
            return HealthStatus(
                provider=provider_name,
                healthy=False,
                last_check=datetime.now(),
                error=str(e)
            )

    def _check_google_elevation(self) -> HealthStatus:
        """Health check for Google Elevation API."""
        import time
        start = time.time()

        try:
            provider = GoogleElevationProvider()
            result = provider.fetch(
                lat=0.0,  # Equator
                lon=0.0,  # Prime meridian
                timeout_s=5
            )
            response_time = (time.time() - start) * 1000

            return HealthStatus(
                provider="google_elevation",
                healthy=result.ok,
                last_check=datetime.now(),
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthStatus(
                provider="google_elevation",
                healthy=False,
                last_check=datetime.now(),
                error=str(e)
            )

    # ... implement checks for other providers
```

**Timeline:** 1.5 weeks
**Owner:** Infrastructure team

---

## Priority 3: Testing and Documentation

### 3.1 Add Integration Tests for All Providers

**File:** `tests/test_providers_integration.py`

```python
import pytest
from datetime import date

class TestElevationProviders:
    """Integration tests for elevation providers."""

    @pytest.mark.network
    def test_google_elevation_sanity(self):
        """Test Google Elevation API with known values."""
        provider = GoogleElevationProvider()

        # Mt. Everest: 27.9881°N, 86.9250°E
        result = provider.fetch(27.9881, 86.9250)

        assert result.ok
        assert 8800 < result.elevation < 8850  # Expected range
        assert result.vertical_datum == "EGM96"

    @pytest.mark.network
    def test_usgs_elevation_sanity(self):
        """Test USGS elevation with known values."""
        provider = USGSElevationProvider()

        # Mt. Everest
        result = provider.fetch(27.9881, 86.9250)

        assert result.ok
        assert 8800 < result.elevation < 8850
        assert result.vertical_datum == "NAVD88"

    @pytest.mark.network
    def test_elevation_fallback_chain(self):
        """Test elevation fallback mechanism."""
        # This test would validate that if one provider fails,
        # the next is tried automatically
        pass

class TestSoilProviders:
    """Integration tests for soil providers."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_soilgrids_completeness(self):
        """Test SoilGrids for data completeness."""
        provider = SoilGridsProvider()

        # Test at a known location (e.g., Iowa cornbelt)
        result = provider.get_soil_data(42.0, -93.0)

        assert result.observations
        obs = result.observations[0]

        # Should have multiple fields
        assert obs.classification_wrb is not None or obs.classification_usda is not None
        assert obs.ph_h2o is not None or obs.organic_carbon is not None

    @pytest.mark.network
    def test_usda_nrcs_us_only(self):
        """Test USDA NRCS limits to US."""
        provider = USDANRCSProvider()

        # US location should work
        result_us = provider.get_soil_data(40.0, -75.0)  # New Jersey
        assert len(result_us.observations) > 0 or result_us.quality_score > 0

        # Non-US location should fail gracefully
        result_non_us = provider.get_soil_data(0.0, 0.0)  # Null Island
        assert len(result_non_us.observations) == 0

class TestMarineProviders:
    """Integration tests for marine providers."""

    @pytest.mark.network
    @pytest.mark.slow
    def test_gebco_bathymetry(self):
        """Test GEBCO bathymetry data."""
        provider = GEBCOProvider()

        # Deep ocean location
        result = provider.get_marine_data(
            latitude=0.0, longitude=-30.0, target_date=date.today()
        )

        assert result.bathymetry is not None
        assert result.bathymetry.value < -1000  # Ocean depths

    @pytest.mark.network
    @pytest.mark.slow
    def test_esa_cci_chlorophyll(self):
        """Test ESA CCI chlorophyll data."""
        provider = ESACCIProvider()

        # Productive ocean region (Gulf Stream)
        result = provider.get_marine_data(
            latitude=40.0, longitude=-70.0,
            target_date=date(2023, 6, 15)
        )

        if result.chlorophyll_a is not None:
            assert 0.001 <= result.chlorophyll_a.value <= 100
```

**Timeline:** 2 weeks
**Owner:** QA team

---

### 3.2 Add Provider Performance Benchmarks

**File:** `tests/test_providers_performance.py`

```python
import pytest
import time
from datetime import date

@pytest.mark.benchmark
class TestProviderPerformance:
    """Benchmark provider response times."""

    @pytest.mark.network
    def test_elevation_response_times(self, benchmark):
        """Benchmark elevation provider response times."""
        provider = OpenTopoDataProvider()

        def fetch():
            return provider.fetch(40.0, -75.0)

        result = benchmark(fetch)
        assert result.ok
        # P95 should be < 2 seconds
        # P99 should be < 5 seconds

    @pytest.mark.network
    def test_geocoding_response_times(self, benchmark):
        """Benchmark geocoding provider response times."""
        provider = OSMForwardGeocodingProvider()

        def search():
            return provider.search("New York City")

        result = benchmark(search)
        assert result.ok
        # P95 should be < 1 second
```

**Timeline:** 1 week
**Owner:** QA team

---

## Success Metrics

### Immediate (Week 1-2)
- [ ] All high-priority fixes deployed
- [ ] USGS provider no longer marked `@pytest.mark.flaky`
- [ ] Marine providers updated to real implementations
- [ ] 100% integration test pass rate

### Short Term (Month 1)
- [ ] Circuit breaker deployed to all providers
- [ ] Health check system operational
- [ ] Retry logic reduces transient failures by 80%
- [ ] All providers have timeout handling

### Medium Term (Month 2)
- [ ] Provider reliability dashboard active
- [ ] SLA tracking for each provider
- [ ] Automated failover mechanisms
- [ ] Documentation of known limitations updated

---

## Rollout Plan

### Phase 1 (Week 1)
1. Deploy circuit breaker pattern
2. Fix USGS retry logic
3. Deploy health checks

### Phase 2 (Week 2-3)
1. Implement ERDDAP clients (marine)
2. Fix GEBCO WCS integration
3. Complete MODIS APPEEARS

### Phase 3 (Week 4)
1. Add comprehensive integration tests
2. Performance benchmarking
3. Documentation update

### Phase 4 (Ongoing)
1. Monitor reliability metrics
2. Adjust configurations based on data
3. Add provider-specific optimizations
