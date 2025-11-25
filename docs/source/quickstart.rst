Quick Start
===========

Get NMDC submission values in 3 steps
--------------------------------------

**Step 1: Install**

.. code-block:: bash

   uv pip install biosample-enricher

**Step 2: Get values**

.. code-block:: python

   from biosample_enricher.submission_values import get_submission_values

   result = get_submission_values(
       lat=37.7749,   # San Francisco
       lon=-122.4194,
       slots=["annual_precpt", "annual_temp"]
   )

   print(result["values"])
   # {'annual_precpt': 519.3, 'annual_temp': 14.1}

**Step 3: Use in your NMDC submission**

The values are already in the correct units and format for NMDC submission-schema.

Next Steps
----------

- **Full guide**: :doc:`submission_values` - Complete documentation with all supported slots
- **Examples**: `examples/ directory <https://github.com/contextualizer-ai/biosample-enricher/tree/main/examples>`_ - Copy-paste ready code
- **Available slots**: See :ref:`what-values-can-you-get` for the complete list

Common Use Cases
----------------

Get climate data
~~~~~~~~~~~~~~~~

.. code-block:: python

   result = get_submission_values(
       lat=42.3601,
       lon=-71.0589,
       slots=["annual_precpt", "annual_temp"]
   )

Get elevation
~~~~~~~~~~~~~

.. code-block:: python

   result = get_submission_values(
       lat=40.7128,
       lon=-74.0060,
       slots=["elev"]
   )

Mix multiple slot types
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = get_submission_values(
       lat=46.7867,
       lon=-121.7365,
       slots=["annual_precpt", "annual_temp", "elev"]
   )

Handle errors
~~~~~~~~~~~~~

.. code-block:: python

   try:
       result = get_submission_values(
           lat=37.7749,
           lon=-122.4194,
           slots=["annual_precpt", "invalid_slot"]
       )
   except ValueError as e:
       print(f"Error: {e}")
       # Error includes list of supported slots

Need Help?
----------

- **Questions?** See the :doc:`submission_values` guide
- **Issues?** `Report on GitHub <https://github.com/contextualizer-ai/biosample-enricher/issues>`_
- **Examples not working?** Check the `examples/ README <https://github.com/contextualizer-ai/biosample-enricher/blob/main/examples/README.md>`_
