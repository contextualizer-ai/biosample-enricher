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

Get NMDC submission-schema values from geographic coordinates. Biosample Enricher retrieves environmental and geographic metadata from authoritative data sources and returns it in the format needed for NMDC submissions.

Features
--------

- **Simple API**: One function - ``get_submission_values(lat, lon, slots)``
- **Multiple Data Sources**: Climate normals, elevation, weather, soil, marine data
- **Multi-Provider Consensus**: Queries multiple providers and returns consensus values
- **Type Safety**: Full type hints with Pydantic validation and mypy checking
- **Smart Caching**: HTTP caching with coordinate canonicalization for efficiency
- **CLI Tool**: Get values without writing code
- **Flexible Installation**: Core functionality only, or add optional mongodb/metrics/schema extras

Installation
------------

.. code-block:: bash

   # Recommended: Use uv
   uv pip install biosample-enricher

   # Or with pip
   pip install biosample-enricher

   # Optional dependencies
   uv pip install biosample-enricher[metrics]   # Metrics and visualization
   uv pip install biosample-enricher[mongodb]   # MongoDB support for NMDC/GOLD
   uv pip install biosample-enricher[all]       # All optional features

Quick Start
-----------

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   # Get NMDC submission values for a location
   result = get_submission_values(
       lat=37.7749,   # San Francisco
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

   print(result["values"])
   # {'annual_precpt': 519.3, 'annual_temp': 14.1, 'elev': 10.2}

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   submission_values
   cli
   services/index

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/api_index
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
