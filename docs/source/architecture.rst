Architecture
============

Core Design
-----------

The biosample-enricher architecture focuses on one primary use case: **retrieving NMDC submission-schema values from geographic coordinates**.

Key Components
--------------

get_submission_values()
~~~~~~~~~~~~~~~~~~~~~~~

The main entry point that orchestrates all data retrieval:

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   result = get_submission_values(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp"]
   )

**See** :doc:`submission_values` for complete documentation.

Multi-Provider System
~~~~~~~~~~~~~~~~~~~~~

Each data type (climate, elevation, etc.) has multiple providers:

- **Climate normals**: meteostat, nasa_power
- **Elevation**: USGS, Google, Open Topo Data, OSM
- **Weather**: meteostat, open-meteo
- **Marine**: GEBCO, ESA CCI, NOAA

The system automatically:

1. Queries multiple providers in parallel
2. Validates and normalizes responses
3. Computes consensus values (median or mean)
4. Returns metadata about which providers were used

**See** :doc:`api/providers` for provider comparison.

HTTP Caching
~~~~~~~~~~~~

All external API calls go through a centralized caching layer using ``requests-cache``:

- **MongoDB primary backend** (with SQLite fallback)
- **Coordinate canonicalization** (4 decimal places)
- **Configurable cache control** via ``read_from_cache``/``write_to_cache`` parameters
- **Automatic TTL management**

Located in: ``biosample_enricher/http_cache.py``

Data Flow
---------

1. **User calls** ``get_submission_values(lat, lon, slots)``
2. **Dispatcher** routes each slot to appropriate service (climate, elevation, etc.)
3. **Service** queries multiple providers via cached HTTP client
4. **Providers** return data in standardized format
5. **Aggregator** computes consensus values
6. **Result** returns values + metadata

Example result structure:

.. code-block:: python

   {
       "values": {
           "annual_precpt": 519.3,
           "annual_temp": 14.1
       },
       "metadata": {
           "climate_normals": {
               "providers_used": ["meteostat", "nasa_power"],
               "provider_results": {
                   "meteostat": {"annual_precpt": 520.1, "annual_temp": 14.0},
                   "nasa_power": {"annual_precpt": 518.5, "annual_temp": 14.2}
               }
           }
       }
   }

Design Principles
-----------------

1. **One way to do it**: ``get_submission_values()`` is THE function
2. **Fail gracefully**: Missing providers don't break the system
3. **Cache aggressively**: Minimize API calls
4. **Type safety**: Full type annotations with mypy strict mode
5. **Test thoroughly**: Unit, integration, and network test categories

Future Development
------------------

Archived code (in ``archived/`` directory) includes:

- MongoDB biosample adapters
- Service-specific CLIs
- Metrics evaluation framework
- Demo scripts

These may be restored when needed. See ``archived/README.md`` for restoration instructions.

Related Documentation
---------------------

- :doc:`submission_values` - Main API documentation
- :doc:`api/providers` - Provider comparison and details
- :doc:`testing` - Testing standards and guidelines
