Models
======

Data models used throughout the biosample-enricher package.

Core Models
-----------

These models are shared across multiple services and represent fundamental concepts.

biosample_enricher.models
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: biosample_enricher.models
   :members:
   :undoc-members:
   :show-inheritance:

Service-Specific Models
------------------------

Each service has its own specialized models for requests and responses.

Weather Models
~~~~~~~~~~~~~~

.. automodule:: biosample_enricher.weather.models
   :members:
   :undoc-members:
   :show-inheritance:

Marine Models
~~~~~~~~~~~~~

.. automodule:: biosample_enricher.marine.models
   :members:
   :undoc-members:
   :show-inheritance:

Soil Models
~~~~~~~~~~~

.. automodule:: biosample_enricher.soil.models
   :members:
   :undoc-members:
   :show-inheritance:

Land Cover Models
~~~~~~~~~~~~~~~~~

.. automodule:: biosample_enricher.land.models
   :members:
   :undoc-members:
   :show-inheritance:

Geocoding Models
~~~~~~~~~~~~~~~~

Forward Geocoding:

.. automodule:: biosample_enricher.forward_geocoding.models
   :members:
   :undoc-members:
   :show-inheritance:

Reverse Geocoding:

.. automodule:: biosample_enricher.reverse_geocoding_models
   :members:
   :undoc-members:
   :show-inheritance:

OSM Features Models
~~~~~~~~~~~~~~~~~~~

.. automodule:: biosample_enricher.osm_features.models
   :members:
   :undoc-members:
   :show-inheritance:

Common Patterns
---------------

All models follow these conventions:

Type Safety
~~~~~~~~~~~

- Full type hints using Python 3.11+ syntax
- Pydantic validation for all external data
- mypy strict mode compliance

Coordinate Handling
~~~~~~~~~~~~~~~~~~~

- Latitude: -90 to 90 decimal degrees
- Longitude: -180 to 180 decimal degrees
- Automatic canonicalization to 4 decimal places (~11m precision)

Observation Pattern
~~~~~~~~~~~~~~~~~~~

Many services return ``Observation`` objects with:

- ``value_numeric``: Numeric measurement (if applicable)
- ``value_string``: String value (if applicable)
- ``provider``: Data source information
- ``metadata``: Additional context

See Also
--------

- :doc:`services` - Service implementations using these models
- :doc:`providers` - Provider-specific response handling
- :doc:`../architecture` - Overall system design
