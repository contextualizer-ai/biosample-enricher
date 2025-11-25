Services Overview
=================

The biosample-enricher package focuses on one primary use case: **retrieving environmental metadata from geographic coordinates**.

Main API
--------

For most users, the only function you need is ``get_environmental_metadata()``:

.. code-block:: python

   from biosample_enricher.environmental_metadata import get_environmental_metadata

   result = get_environmental_metadata(
       lat=37.7749,
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

**Full documentation**: :doc:`../environmental_metadata`

**CLI access**: :doc:`../cli`

Underlying Services (Advanced)
------------------------------

The ``get_environmental_metadata()`` function coordinates multiple specialized services internally:

- **Climate service**: Annual precipitation and temperature normals (meteostat, nasa_power)
- **Elevation service**: Elevation above sea level (usgs, google, open_topo_data, osm)
- **Weather service**: Point-in-time weather data (meteostat, open_meteo)
- **Marine service**: Ocean depth (gebco, noaa)
- **Soil service**: Soil properties (soilgrids, usda_nrcs)

These services are abstracted away for simplicity. Most users should use ``get_environmental_metadata()`` rather than calling services directly.

For advanced users who need direct service access, see:

- :doc:`../api/services` - Service API reference
- :doc:`../api/providers` - Provider comparison
- :doc:`../architecture` - System architecture
