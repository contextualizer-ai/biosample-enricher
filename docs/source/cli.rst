CLI Reference
=============

The ``biosample-enricher`` CLI provides command-line access to ``get_submission_values()``.

Installation
------------

.. code-block:: bash

   # Installation includes CLI
   uv add biosample-enricher

   # Or with pip
   pip install biosample-enricher

Commands Overview
-----------------

.. code-block:: bash

   biosample-enricher --help          # Show all commands
   biosample-enricher get --help      # Get submission values
   biosample-enricher info            # Show available slots and providers
   biosample-enricher slots           # List slot names (for scripting)
   biosample-enricher providers       # List providers (for scripting)
   biosample-enricher strategies      # List consensus strategies

biosample-enricher get
----------------------

The main command for retrieving NMDC submission values.

**Basic Usage:**

.. code-block:: bash

   # Get climate and elevation data
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt,annual_temp,elev

   # Get all supported slots
   biosample-enricher get --lat 37.7749 --lon -122.4194 --slots all

**Options:**

.. code-block:: text

   --lat FLOAT              Latitude in decimal degrees (-90 to 90) [required]
   --lon FLOAT              Longitude in decimal degrees (-180 to 180) [required]
   --slots TEXT             Comma-separated slot names, or "all" [required]
   --datetime TEXT          Collection datetime for weather slots (ISO format)
   --providers TEXT         Comma-separated provider names (default: all)
   --strategy [mean|median|first|best_quality]
                            Consensus strategy (default: mean)
   --output PATH            Output file path (default: stdout)
   --pretty / --compact     Pretty-print JSON output (default: pretty)
   --values-only            Output only the values dict, not metadata

**Examples:**

.. code-block:: bash

   # Basic climate + elevation
   biosample-enricher get \
       --lat 42.3601 \
       --lon -71.0589 \
       --slots annual_precpt,annual_temp,elev

   # Weather data (requires datetime)
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots temp,humidity \
       --datetime 2023-07-15

   # Use median consensus instead of mean
   biosample-enricher get \
       --lat 40.7128 \
       --lon -74.0060 \
       --slots elev \
       --strategy median

   # Use specific providers only
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt \
       --providers meteostat

   # Output to file
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt,elev \
       --output values.json

   # Compact JSON (for piping)
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt \
       --compact

   # Values only (no metadata)
   biosample-enricher get \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt,elev \
       --values-only

biosample-enricher info
-----------------------

Show available slots, providers, and consensus strategies.

.. code-block:: bash

   # Human-readable format (default)
   biosample-enricher info

   # JSON format (for scripting)
   biosample-enricher info --format json

biosample-enricher slots
------------------------

List all supported slot names (one per line, for scripting).

.. code-block:: bash

   biosample-enricher slots
   # air_temp
   # annual_precpt
   # annual_temp
   # ...

biosample-enricher providers
----------------------------

List available providers.

.. code-block:: bash

   # All providers
   biosample-enricher providers

   # Filter by category
   biosample-enricher providers --category climate
   biosample-enricher providers --category elevation

biosample-enricher strategies
-----------------------------

List consensus strategies.

.. code-block:: bash

   biosample-enricher strategies
   # best_quality
   # first
   # mean
   # median

Available Slots
---------------

See :ref:`quick-reference` in the submission values documentation for the complete list.

**Quick reference:**

- **Climate** (no datetime needed): ``annual_precpt``, ``annual_temp``
- **Elevation**: ``elev``
- **Weather** (datetime required): ``temp``, ``air_temp``, ``humidity``, ``wind_speed``, ``wind_direction``, ``solar_irradiance``
- **Marine**: ``depth``
- **Soil**: ``ph``, ``soil_type``

Python API Alternative
----------------------

For programmatic access, use the Python API:

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   result = get_submission_values(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp"]
   )

See :doc:`submission_values` for complete Python API documentation.

Troubleshooting
---------------

**"Unsupported slot" error**

The slot name isn't supported. Run ``biosample-enricher info`` to see available slots.

**"Invalid coordinates" error**

Latitude must be -90 to 90, longitude must be -180 to 180.

**"datetime_obj required" error**

Weather slots (``temp``, ``humidity``, etc.) require the ``--datetime`` option.

**No data returned for a slot**

Some slots may not have data for all locations. The slot will be omitted from results.
Check the metadata to see which providers were queried and any errors.

Related Documentation
---------------------

- :doc:`submission_values` - Full Python API documentation
- :doc:`quickstart` - Quick start guide
