Services Overview
=================

The biosample-enricher package focuses on one primary use case: **retrieving NMDC submission-schema values from geographic coordinates**.

Main API
--------

For most users, the only function you need is ``get_submission_values()``:

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   result = get_submission_values(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

**Full documentation**: :doc:`../submission_values`

**CLI access**: :doc:`../cli`

Underlying Services (Advanced)
------------------------------

The ``get_submission_values()`` function coordinates multiple specialized services internally:

- **Climate service**: Annual precipitation and temperature normals (meteostat, nasa_power)
- **Elevation service**: Elevation above sea level (usgs, google, open_topo_data, osm)
- **Weather service**: Point-in-time weather data (meteostat, open_meteo)
- **Marine service**: Ocean depth (gebco, noaa)
- **Soil service**: Soil properties (soilgrids, usda_nrcs)

These services are abstracted away for simplicity. Most users should use ``get_submission_values()`` rather than calling services directly.

For advanced users who need direct service access, see:

- :doc:`../api/services` - Service API reference
- :doc:`../api/providers` - Provider comparison
- :doc:`../architecture` - System architecture
