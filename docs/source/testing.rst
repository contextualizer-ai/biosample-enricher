Testing
=======

Comprehensive testing guide for biosample-enricher.

.. include:: ../TESTING.md
   :parser: myst_parser.sphinx_

Quick Start
-----------

**Run all tests:**

.. code-block:: bash

   uv run pytest

**Run with coverage:**

.. code-block:: bash

   uv run pytest --cov=biosample_enricher --cov-report=term-missing

**Skip network tests (fast):**

.. code-block:: bash

   uv run pytest -m "not network"

**Run only network tests:**

.. code-block:: bash

   uv run pytest -m network

Test Categories
---------------

Tests are marked with categories:

- ``@pytest.mark.unit`` - Fast, isolated, no external dependencies
- ``@pytest.mark.integration`` - Multiple components, mocked externals
- ``@pytest.mark.network`` - Real API calls (skipped in CI)
- ``@pytest.mark.slow`` - Performance/timing tests
- ``@pytest.mark.flaky`` - Known intermittent failures (see :doc:`provider_reliability`)

Related Documentation
---------------------

- `Flaky Tests <https://github.com/contextualizer-ai/biosample-enricher/blob/main/docs/flaky-tests.md>`_ - Known test reliability issues
- :doc:`provider_reliability` - Provider stability analysis
- :doc:`contributing` - How to contribute tests
