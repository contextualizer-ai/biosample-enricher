"""Metrics module for evaluating biosample enrichment coverage.

This module uses lazy imports for components that require optional dependencies
(matplotlib, seaborn) to avoid forcing all users to install visualization libraries.
"""

from typing import Any

# Core imports that don't require optional dependencies
from biosample_enricher.metrics.evaluator import CoverageEvaluator
from biosample_enricher.metrics.fetcher import BiosampleMetricsFetcher
from biosample_enricher.metrics.reporter import MetricsReporter

__all__ = [
    "BiosampleMetricsFetcher",
    "CoverageEvaluator",
    "MetricsReporter",
    "MetricsVisualizer",
    "generate_html_dashboard",
    "generate_metrics_report",
]


def __getattr__(name: str) -> Any:
    """Lazy import for visualization components requiring optional dependencies.

    This allows the metrics module to be imported without matplotlib/seaborn,
    while still providing access to visualization features when needed.
    """
    if name == "MetricsVisualizer":
        from biosample_enricher.metrics.visualizer import MetricsVisualizer

        return MetricsVisualizer
    elif name == "generate_html_dashboard":
        from biosample_enricher.metrics.dashboard import generate_html_dashboard

        return generate_html_dashboard
    elif name == "generate_metrics_report":
        from biosample_enricher.metrics.markdown import generate_metrics_report

        return generate_metrics_report
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
