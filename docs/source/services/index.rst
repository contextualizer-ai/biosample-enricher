Getting NMDC Submission Values
===============================

.. important::
   **Looking for how to get NMDC submission values?**

   The main function you need is :doc:`../submission_values`.

The biosample-enricher package focuses on one primary use case: **retrieving NMDC submission-schema values from geographic coordinates**.

Quick Example
-------------

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   result = get_submission_values(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

   print(result["values"])
   # {'annual_precpt': 519.3, 'annual_temp': 14.1, 'elev': 10.2}

See the Complete Guide
-----------------------

:doc:`../submission_values`
   Complete documentation for ``get_submission_values()`` including:

   - All supported slots
   - Parameter details
   - Return value structure
   - Error handling
   - Examples

:doc:`../cli`
   Command-line interface for getting values without writing code

:doc:`../api/providers`
   Details about data providers for each slot type

Underlying Services
-------------------

The ``get_submission_values()`` function coordinates multiple specialized services:

- **Climate service**: Annual precipitation and temperature normals
- **Elevation service**: Elevation above sea level
- **Weather service**: Current/historical weather data (requires datetime)
- **Marine service**: Ocean depth and conditions
- **Soil service**: Soil properties
- **Geocoding services**: Location names and geographic features

These services are abstracted away for simplicity, but you can read about their internal architecture in :doc:`../architecture`.

CLI Tools
---------

Use the main CLI for most tasks:

.. code-block:: bash

   biosample-enricher --lat 37.7749 --lon -122.4194 --slots annual_precpt annual_temp

See :doc:`../cli` for complete CLI documentation.

Related Documentation
---------------------

- :doc:`../quickstart` - Get started in 3 steps
- :doc:`../architecture` - System architecture overview
- :doc:`../api/services` - Service API reference (advanced users)
