Environmental Metadata
======================

.. currentmodule:: biosample_enricher.environmental_metadata

Get environmental metadata for geographic coordinates.

What It Does
------------

**Get environmental metadata values** for slots like ``annual_precpt``, ``annual_temp``, ``elev``, ``depth``, etc.

Give it GPS coordinates → Get back values with units and provenance. Compatible with NMDC submission-schema and other applications.

Quick Example
-------------

.. code-block:: python

   from biosample_enricher.environmental_metadata import get_environmental_metadata

   # Get climate data for San Francisco
   result = get_environmental_metadata(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp"]
   )

   # Use the values in your NMDC submission
   print(result["values"])
   # {'annual_precpt': 519.3, 'annual_temp': 14.1}

   # Check which data sources were used
   print(result["metadata"]["climate_normals"]["providers_used"])
   # ['meteostat', 'nasa_power']

What Values Can You Get?
-------------------------

Currently Supported (✅ Ready to Use)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Climate Data** (30-year averages, no datetime needed):

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Slot Name
     - Description
     - Units
     - Type
   * - ``annual_precpt``
     - Annual precipitation (30-year average)
     - millimeters/year
     - float
   * - ``annual_temp``
     - Annual temperature (30-year average)
     - degrees Celsius
     - float

**Providers**: meteostat, nasa_power (automatically queries both and averages results)

**Elevation Data** (no datetime needed):

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Slot Name
     - Description
     - Units
     - Type
   * - ``elev``
     - Elevation above sea level
     - meters
     - float

**Providers**: USGS, Google Maps, Open Topo Data, OSM (tries multiple sources)

Partially Implemented (⚠️ Use with Caution)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Weather Data** (requires datetime - collection date/time):

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Slot Name
     - Description
     - Units
     - Type
   * - ``temp``
     - Temperature at collection time
     - degrees Celsius
     - float
   * - ``air_temp``
     - Air temperature (alias for temp)
     - degrees Celsius
     - float
   * - ``humidity``
     - Relative humidity
     - g/m³
     - string
   * - ``wind_speed``
     - Wind speed
     - m/s
     - string
   * - ``wind_direction``
     - Wind direction
     - degrees
     - string
   * - ``solar_irradiance``
     - Solar radiation
     - W/m²
     - string

.. warning::
   Weather slots require ``datetime_obj`` parameter. Data availability depends on location and date.
   Not all slots may return values for all locations/times.

**Marine Data** (no datetime needed):

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Slot Name
     - Description
     - Units
     - Type
   * - ``depth``
     - Water depth (negative for underwater)
     - meters
     - string

.. warning::
   Marine providers (GEBCO, ESA CCI, NOAA) are marked as unreliable in Issue #181.
   Data quality varies significantly by location.

**Soil Data** (no datetime needed):

.. list-table::
   :header-rows: 1
   :widths: 20 50 15 15

   * - Slot Name
     - Description
     - Units
     - Type
   * - ``ph``
     - Soil pH
     - pH units
     - float
   * - ``soil_type``
     - USDA soil texture class
     - text
     - string

.. warning::
   SoilGrids provider has intermittent failures (Issue #184). Success rate varies by location.

Not Yet Implemented (❌ Future Work)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These submission-schema slots are **not yet supported**:

- ``cur_vegetation`` - Current vegetation type (Issue #194)
- ``flooding`` - Flooding history (Issue #192)
- ``fire`` - Fire history
- ``extreme_event`` - Extreme weather events
- Many others...

See the `submission-schema documentation <https://microbiomedata.github.io/nmdc-schema/>`_ for the complete list of slots.

.. seealso::
   Issue #193: Add submission-schema extraction helpers for more slots

Parameters
----------

.. function:: get_environmental_metadata(lat, lon, slots, datetime_obj=None, providers=None, strategy="mean")

   Get NMDC submission-schema values for specified slots.

   :param float lat: Latitude in decimal degrees (required)
                     Valid range: -90 to 90

   :param float lon: Longitude in decimal degrees (required)
                     Valid range: -180 to 180

   :param list[str] slots: Slot names to retrieve (required)
                          Must be from supported slots listed above.
                          Cannot be empty.

                          **Examples**::

                            # Climate only
                            slots=["annual_precpt", "annual_temp"]

                            # Mix climate and elevation
                            slots=["annual_precpt", "elev"]

                            # Weather (requires datetime_obj)
                            slots=["temp", "humidity", "wind_speed"]

   :param datetime datetime_obj: Collection date/time (optional)
                                 **Required for weather slots** (temp, air_temp, humidity, etc.)
                                 Not used for climate, elevation, marine, or soil slots

                                 **Example**::

                                   from datetime import datetime
                                   datetime_obj=datetime(2023, 7, 15, 14, 30)

   :param list[str] providers: Specific providers to use (optional)
                               If None (default), queries all available providers.

                               **Valid providers by slot category:**

                               - Climate slots: ``["meteostat", "nasa_power"]``
                               - Elevation slots: ``["usgs", "google", "open_topo_data", "osm"]``

                               **Examples**::

                                 # Use only meteostat for climate
                                 providers=["meteostat"]

                                 # Use only USGS for elevation
                                 providers=["usgs"]

   :param str strategy: How to combine values from multiple providers (optional)
                        Default is ``"mean"``.

                        **Valid values** (from ``CONSENSUS_STRATEGIES``):

                        - ``"mean"``: Average across all successful providers (default, most reliable)
                        - ``"median"``: Middle value when sorted (robust to outliers)
                        - ``"first"``: Use first successful provider in priority order (fastest)
                        - ``"best_quality"``: Use provider with best quality metric (closest station, highest resolution)

                        See :ref:`consensus-strategies` for detailed descriptions and usage guidance.

                        **Example**::

                          # Use median to handle outliers
                          result = get_environmental_metadata(
                              lat=46.8523, lon=-121.7603,
                              slots=["elev"],
                              strategy="median"
                          )

   :returns: Dictionary with two keys:

             - ``"values"``: Dict mapping slot names to submission-ready values

               - Values are in the correct units for submission-schema
               - Slots that failed to retrieve data are **omitted** (not None)
               - Types match submission-schema requirements (mostly float, some string)

             - ``"metadata"``: Dict with provider information for transparency

               - Shows which data sources contributed to each value
               - Includes provider-specific results for comparison
               - Lists any providers that failed with error messages

   :rtype: dict[str, Any]

   :raises ValueError: If latitude is outside -90 to 90
   :raises ValueError: If longitude is outside -180 to 180
   :raises ValueError: If slots list is empty
   :raises ValueError: If slots contains unsupported slot names
                       (Error message will list all supported slots)
   :raises ValueError: If providers contains invalid provider names for requested slots
                       (Error message will list valid providers)

Return Value Structure
----------------------

The function returns a dictionary with this structure:

.. code-block:: python

   {
       "values": {
           "annual_precpt": 519.3,      # float: mm/year
           "annual_temp": 14.1,          # float: °C
           "elev": 52.4                  # float: meters
           # Missing/failed slots are omitted
       },
       "metadata": {
           "climate_normals": {          # Only present if climate slots requested
               "providers_used": ["meteostat", "nasa_power"],
               "consensus_strategy": "consensus",  # How values were combined
               "provider_results": {
                   "meteostat": {
                       "annual_precpt": 453.1,
                       "annual_temp": 14.2,
                       "period": "1991-2020",
                       "station_distance_km": 3.2
                   },
                   "nasa_power": {
                       "annual_precpt": 585.5,
                       "annual_temp": 14.0,
                       "period": "2001-2020"
                   }
               },
               "failed_providers": {}     # Dict of {provider: error_message}
           }
           # "weather", "elevation", "marine", "soil" metadata added as implemented
       }
   }

.. note::
   **Missing slots are omitted**, not set to None. Always check with ``if "slot_name" in result["values"]``
   before accessing values.

Examples
--------

Basic Climate Data
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from biosample_enricher.environmental_metadata import get_environmental_metadata

   # Get 30-year climate averages for a location
   result = get_environmental_metadata(
       lat=42.3601,   # Boston
       lon=-71.0589,
       slots=["annual_precpt", "annual_temp"]
   )

   # Use the values
   precip = result["values"]["annual_precpt"]  # 1090.2 mm/year
   temp = result["values"]["annual_temp"]      # 10.8 °C

   # Check data quality by comparing providers
   providers = result["metadata"]["climate_normals"]["provider_results"]
   for name, data in providers.items():
       print(f"{name}: {data['annual_precpt']:.1f} mm/year")
   # meteostat: 1089.3 mm/year
   # nasa_power: 1091.1 mm/year

Mixing Multiple Slot Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get climate + elevation in one call
   result = get_environmental_metadata(
       lat=40.7128,   # New York City
       lon=-74.0060,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

   values = result["values"]
   print(f"Elevation: {values['elev']} m")
   print(f"Annual rain: {values['annual_precpt']} mm/year")
   print(f"Annual temp: {values['annual_temp']} °C")

Using Specific Providers
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use only meteostat for climate (not NASA POWER)
   result = get_environmental_metadata(
       lat=51.5074,   # London
       lon=-0.1278,
       slots=["annual_precpt", "annual_temp"],
       providers=["meteostat"]  # Only use this provider
   )

   metadata = result["metadata"]["climate_normals"]
   print(metadata["providers_used"])  # ['meteostat']

Weather Data (Requires Datetime)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from datetime import datetime

   # Get weather at sample collection time
   result = get_environmental_metadata(
       lat=34.0522,   # Los Angeles
       lon=-118.2437,
       slots=["temp", "humidity", "wind_speed"],
       datetime_obj=datetime(2023, 7, 15, 14, 30)  # Required!
   )

   # Check what data was available
   if "temp" in result["values"]:
       print(f"Temperature: {result['values']['temp']} °C")
   else:
       print("Temperature data not available for this location/time")

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   # Handle invalid inputs gracefully
   try:
       result = get_environmental_metadata(
           lat=37.7749,
           lon=-122.4194,
           slots=["annual_precpt", "invalid_slot_name"]
       )
   except ValueError as e:
       print(f"Error: {e}")
       # Error: Unsupported slot(s): ['invalid_slot_name'].
       # Supported slots: ['air_temp', 'annual_precpt', 'annual_temp', ...]

   # Check for missing data
   result = get_environmental_metadata(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "depth"]  # depth may not be available on land
   )

   if "annual_precpt" in result["values"]:
       print(f"Got precipitation: {result['values']['annual_precpt']}")

   if "depth" not in result["values"]:
       print("Depth data not available (probably on land)")

.. _quick-reference:

Quick Reference
---------------

All Constants at a Glance
~~~~~~~~~~~~~~~~~~~~~~~~~

These constants are available for programmatic access:

.. code-block:: python

   from biosample_enricher.environmental_metadata import (
       # Slot categories
       ALL_SUPPORTED_SLOTS,   # All slots combined
       CLIMATE_SLOTS,         # {'annual_precpt', 'annual_temp'}
       WEATHER_SLOTS,         # {'temp', 'air_temp', 'humidity', 'wind_speed', 'wind_direction', 'solar_irradiance'}
       ELEVATION_SLOTS,       # {'elev'}
       MARINE_SLOTS,          # {'depth'}
       SOIL_SLOTS,            # {'ph', 'soil_type'}

       # Provider names
       CLIMATE_PROVIDERS,     # {'meteostat', 'nasa_power'}
       ELEVATION_PROVIDERS,   # {'usgs', 'google', 'open_topo_data', 'osm'}

       # Consensus strategies
       CONSENSUS_STRATEGIES,  # {'mean', 'median', 'first', 'best_quality'}
   )

Slots by Category
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 40 20 20

   * - Category
     - Slots
     - Providers
     - Datetime Required?
   * - Climate
     - ``annual_precpt``, ``annual_temp``
     - meteostat, nasa_power
     - No
   * - Weather
     - ``temp``, ``air_temp``, ``humidity``, ``wind_speed``, ``wind_direction``, ``solar_irradiance``
     - meteostat, open_meteo
     - **Yes**
   * - Elevation
     - ``elev``
     - usgs, google, open_topo_data, osm
     - No
   * - Marine
     - ``depth``
     - gebco, noaa
     - No
   * - Soil
     - ``ph``, ``soil_type``
     - soilgrids, usda_nrcs
     - No

.. _consensus-strategies:

Consensus Strategies
~~~~~~~~~~~~~~~~~~~~

When multiple providers return data, values are combined using a consensus strategy:

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - Strategy
     - Description
     - When to Use
   * - ``mean``
     - Arithmetic average across all providers (default)
     - General use, most reliable
   * - ``median``
     - Middle value when sorted
     - When outliers are possible
   * - ``first``
     - Use first successful provider
     - When speed matters
   * - ``best_quality``
     - Use provider with best quality metric
     - Advanced use with quality scores

Slot Status (Reliability)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 35 50

   * - Status
     - Slots
     - Notes
   * - **Ready**
     - ``annual_precpt``, ``annual_temp``, ``elev``
     - Production-ready, reliable data
   * - **Caution**
     - ``temp``, ``ph``, ``depth``
     - May have gaps or provider issues
   * - **Experimental**
     - ``air_temp``, ``humidity``, ``wind_speed``, ``wind_direction``, ``solar_irradiance``, ``soil_type``
     - Limited testing, may change

Copy-Paste Slot Lists
~~~~~~~~~~~~~~~~~~~~~

For convenience, here are the slot names ready to copy:

**All slots (comma-separated)**::

   annual_precpt, annual_temp, elev, temp, air_temp, humidity, wind_speed, wind_direction, solar_irradiance, depth, ph, soil_type

**Production-ready slots only**::

   annual_precpt, annual_temp, elev

**Climate + Elevation (most common)**::

   annual_precpt, annual_temp, elev

Checking Available Slots and Providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from biosample_enricher.environmental_metadata import (
       ALL_SUPPORTED_SLOTS,
       CLIMATE_SLOTS,
       WEATHER_SLOTS,
       ELEVATION_SLOTS,
       MARINE_SLOTS,
       SOIL_SLOTS,
       CLIMATE_PROVIDERS,
       ELEVATION_PROVIDERS,
       CONSENSUS_STRATEGIES,
   )

   # See all supported slots
   print("All slots:", sorted(ALL_SUPPORTED_SLOTS))

   # See slots by category
   print("Climate:", sorted(CLIMATE_SLOTS))
   print("Weather:", sorted(WEATHER_SLOTS))
   print("Elevation:", sorted(ELEVATION_SLOTS))
   print("Marine:", sorted(MARINE_SLOTS))
   print("Soil:", sorted(SOIL_SLOTS))

   # See available providers
   print("Climate providers:", sorted(CLIMATE_PROVIDERS))
   print("Elevation providers:", sorted(ELEVATION_PROVIDERS))

   # See consensus strategies
   print("Strategies:", sorted(CONSENSUS_STRATEGIES))

Limitations and Known Issues
-----------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

1. **Limited slot coverage**: Only 13 of ~200+ submission-schema slots are supported
2. **No bulk operations**: Must call once per biosample (no batch processing yet)
3. **Weather data gaps**: Historical weather not available for all locations/times
4. **Provider reliability**: Some providers have intermittent failures (see issues below)
5. **No caching control**: Cannot disable or clear HTTP cache from this function

Known Issues
~~~~~~~~~~~~

.. warning::
   **Provider Reliability Issues** - Please review these before relying on data:

   - Issue #181: Marine providers (GEBCO, ESA CCI, NOAA) incomplete/unreliable
   - Issue #182: MODIS vegetation provider uses mock data only
   - Issue #183: USGS elevation provider unreliable (marked flaky)
   - Issue #184: SoilGrids provider intermittent failures (marked flaky)

   Climate and elevation data are generally reliable. Marine and soil data quality varies.

Future Development
~~~~~~~~~~~~~~~~~~

These features are **planned but not yet implemented**:

- More submission-schema slots (Issue #193)
- Vegetation data from land cover (Issue #194)
- Flooding history (Issue #192)
- Batch processing for multiple biosamples
- Quality scores and confidence intervals
- Custom provider selection strategies beyond "consensus"

See Also
--------

**For Advanced Users:**

- :doc:`api/services` - Low-level service APIs for more control
- :doc:`api/providers` - Individual provider documentation
- :doc:`provider_reliability` - Provider stability and quality metrics

**For Understanding the Code:**

- :doc:`api/api_index` - Complete API reference
- :doc:`architecture` - System design and data flow

**External Resources:**

- `NMDC Submission Schema <https://microbiomedata.github.io/nmdc-schema/>`_ - Official schema documentation
- `GOLD Biosample Fields <https://gold.jgi.doe.gov/>`_ - Related biosample metadata standard
