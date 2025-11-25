CLI Reference
=============

The main CLI for getting NMDC submission values.

biosample-enricher
------------------

Main command-line interface for retrieving NMDC submission-schema values.

.. code-block:: bash

   # Installation includes CLI
   uv pip install biosample-enricher

   # Get help
   biosample-enricher --help

Usage
~~~~~

**Get climate data:**

.. code-block:: bash

   biosample-enricher \
       --lat 37.7749 \
       --lon -122.4194 \
       --slots annual_precpt annual_temp

**Get multiple slot types:**

.. code-block:: bash

   biosample-enricher \
       --lat 40.7128 \
       --lon -74.0060 \
       --slots annual_precpt annual_temp elev

**Output to file:**

.. code-block:: bash

   biosample-enricher \
       --lat 42.3601 \
       --lon -71.0589 \
       --slots annual_precpt annual_temp \
       --output values.json

Options
~~~~~~~

.. code-block:: text

   --lat FLOAT              Latitude in decimal degrees (required)
   --lon FLOAT              Longitude in decimal degrees (required)
   --slots TEXT [TEXT ...]  Submission-schema slot names (required)
   --output PATH            Output file path (default: stdout)
   --providers TEXT [...]   Specific providers to use (optional)
   --help                   Show help message

Available Slots
~~~~~~~~~~~~~~~

See :doc:`submission_values` for the complete list of supported slots.

Quick reference:

- **Climate**: annual_precpt, annual_temp
- **Elevation**: elev
- **Marine**: depth
- **Soil**: ph, soil_type
- **Weather**: temp, humidity, wind_speed, wind_direction, solar_irradiance

Python API Alternative
----------------------

For programmatic access, use the Python API instead:

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

The slot name you provided isn't supported. Check the available slots above or run:

.. code-block:: bash

   biosample-enricher --help

**"Invalid coordinates" error**

Latitude must be -90 to 90, longitude must be -180 to 180.

**No data returned for a slot**

Some slots may not have data available for all locations. This is normal - the slot will be omitted from results.

Related Documentation
---------------------

- :doc:`submission_values` - Full Python API documentation
- :doc:`quickstart` - Quick start guide
- `Examples <https://github.com/contextualizer-ai/biosample-enricher/tree/main/examples>`_ - Sample code
