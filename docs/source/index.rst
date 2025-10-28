Biosample Enricher Documentation
===================================

Infer AI-friendly environmental and geographic metadata about biosamples from multiple sources.

.. image:: https://img.shields.io/badge/python-3.11%2B-blue.svg
   :target: https://python.org
   :alt: Python Version

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

.. image:: https://img.shields.io/pypi/v/biosample-enricher
   :target: https://pypi.org/project/biosample-enricher/
   :alt: PyPI version

Overview
--------

Biosample Enricher provides 8 specialized services for enriching biosample metadata with environmental and geographic information from authoritative data sources. Each service focuses on a specific domain and returns structured, type-safe data ready for analysis or AI applications.

Features
--------

- **8 Specialized Services**: Elevation, soil, weather, marine, land cover, forward/reverse geocoding, geographic features
- **Service-Based Architecture**: Independent services with focused responsibilities
- **Type Safety**: Full type hints with Pydantic validation and mypy checking
- **Smart Caching**: HTTP caching with coordinate canonicalization for efficiency
- **Multiple Providers**: Automatic fallback between data providers (USGS, Google, OSM, etc.)
- **Click-Based CLIs**: User-friendly command-line tools for each service
- **Flexible Installation**: Core services only, or add optional mongodb/metrics/schema extras

Installation
------------

Using UV (Recommended)
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Basic installation - all 8 enrichment services
   uv add biosample-enricher

   # With optional dependencies
   uv add biosample-enricher --extra metrics   # Metrics and visualization
   uv add biosample-enricher --extra mongodb   # MongoDB support for NMDC/GOLD
   uv add biosample-enricher --extra schema    # Schema analysis tools
   uv add biosample-enricher --extra all       # All optional features

Using Pip
^^^^^^^^^

.. code-block:: bash

   pip install biosample-enricher
   pip install biosample-enricher[metrics]

Quick Start
-----------

.. code-block:: python

   from biosample_enricher import ElevationService, ElevationRequest

   # Get elevation for a location
   service = ElevationService()
   request = ElevationRequest(latitude=40.7128, longitude=-74.0060)
   observations = service.get_elevation(request)

   for obs in observations:
       if obs.value_numeric is not None:
           print(f"{obs.provider.name}: {obs.value_numeric}m")

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   services/index
   cli

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/services
   api/models
   api/providers

.. toctree::
   :maxdepth: 1
   :caption: Developer Guide

   contributing
   architecture
   testing
   provider_reliability

.. toctree::
   :maxdepth: 1
   :caption: Project Info

   changelog
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
