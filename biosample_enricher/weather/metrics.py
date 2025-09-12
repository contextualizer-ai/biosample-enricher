"""
Weather enrichment metrics for before/after coverage analysis.

Tracks weather field coverage improvements across biosample sources
and generates comprehensive metrics for weather enrichment evaluation.
"""

from collections import defaultdict
from typing import Any

import pandas as pd

from biosample_enricher.logging_config import get_logger
from biosample_enricher.weather.service import WeatherService

logger = get_logger(__name__)


class WeatherEnrichmentMetrics:
    """
    Tracks and analyzes weather enrichment coverage metrics.

    Provides before/after analysis for weather field coverage across
    different biosample sources (NMDC, GOLD) and environmental realms.
    """

    # Weather fields tracked for coverage analysis
    WEATHER_FIELDS = {
        "temperature": ["temp", "avg_temp", "sampleCollectionTemperature"],
        "wind_speed": ["wind_speed"],
        "wind_direction": ["wind_direction"],
        "humidity": ["humidity", "abs_air_humidity"],
        "solar_radiation": ["solar_irradiance", "photon_flux"],
        "precipitation": ["precipitation"],  # New field
        "pressure": ["pressure"],
    }

    def __init__(self):
        self.weather_service = WeatherService()
        self.enrichment_results = []
        self.coverage_stats = {
            "before": defaultdict(lambda: defaultdict(int)),
            "after": defaultdict(lambda: defaultdict(int)),
        }

    def analyze_biosample_collection(
        self, biosamples: list[dict[str, Any]], source: str = "unknown"
    ) -> dict[str, Any]:
        """
        Analyze weather field coverage before and after enrichment for a collection of biosamples.

        Args:
            biosamples: List of biosample dictionaries
            source: Source identifier ("nmdc", "gold", etc.)

        Returns:
            Dict with comprehensive before/after coverage analysis
        """
        logger.info(
            f"Starting weather enrichment analysis for {len(biosamples)} {source} biosamples"
        )

        before_coverage = self._analyze_existing_coverage(biosamples, source)
        after_coverage = self._analyze_enriched_coverage(biosamples, source)

        improvement_analysis = self._calculate_improvements(
            before_coverage, after_coverage
        )

        return {
            "source": source,
            "sample_count": len(biosamples),
            "before_coverage": before_coverage,
            "after_coverage": after_coverage,
            "improvements": improvement_analysis,
            "enrichment_summary": self._generate_enrichment_summary(source),
        }

    def _analyze_existing_coverage(
        self, biosamples: list[dict[str, Any]], source: str
    ) -> dict[str, float]:
        """Analyze existing weather field coverage in biosamples."""
        logger.info(f"Analyzing existing weather coverage for {source}")

        field_counts: dict[str, int] = defaultdict(int)
        total_samples = len(biosamples)

        for biosample in biosamples:
            for weather_param, schema_fields in self.WEATHER_FIELDS.items():
                has_field = False

                for schema_field in schema_fields:
                    if self._has_weather_data(biosample, schema_field):
                        has_field = True
                        break

                if has_field:
                    field_counts[weather_param] += 1

        # Calculate coverage percentages
        coverage_percentages = {}
        for weather_param in self.WEATHER_FIELDS:
            coverage_percentages[weather_param] = (
                (field_counts[weather_param] / total_samples) * 100
                if total_samples > 0
                else 0
            )

        # Store in tracking structure
        for weather_param, percentage in coverage_percentages.items():
            self.coverage_stats["before"][source][weather_param] = percentage

        return coverage_percentages

    def _analyze_enriched_coverage(
        self, biosamples: list[dict[str, Any]], source: str
    ) -> dict[str, float]:
        """Analyze weather field coverage after enrichment."""
        logger.info(f"Performing weather enrichment for {source}")

        enriched_samples = []
        successful_enrichments = 0
        failed_enrichments = 0

        for i, biosample in enumerate(biosamples):
            try:
                # Attempt weather enrichment
                enrichment_result = self.weather_service.get_weather_for_biosample(
                    biosample,
                    target_schema="nmdc" if source.lower() == "nmdc" else "gold",
                )

                if enrichment_result["enrichment_success"]:
                    successful_enrichments += 1

                    # Create enriched biosample with new weather data
                    enriched_biosample = biosample.copy()
                    enriched_biosample.update(enrichment_result["schema_mapping"])
                    enriched_samples.append(enriched_biosample)

                    # Store enrichment result for detailed analysis
                    self.enrichment_results.append(
                        {
                            "source": source,
                            "sample_index": i,
                            "biosample_id": biosample.get("id", f"sample_{i}"),
                            "weather_result": enrichment_result["weather_result"],
                            "coverage_metrics": enrichment_result["coverage_metrics"],
                        }
                    )
                else:
                    failed_enrichments += 1
                    enriched_samples.append(biosample)  # Keep original

            except Exception as e:
                logger.warning(
                    f"Weather enrichment failed for {source} sample {i}: {e}"
                )
                failed_enrichments += 1
                enriched_samples.append(biosample)  # Keep original

        logger.info(
            f"Weather enrichment completed: {successful_enrichments} successful, {failed_enrichments} failed"
        )

        # Analyze coverage in enriched samples
        field_counts: dict[str, int] = defaultdict(int)
        total_samples = len(enriched_samples)

        for enriched_biosample in enriched_samples:
            for weather_param, schema_fields in self.WEATHER_FIELDS.items():
                has_field = False

                for schema_field in schema_fields:
                    if self._has_weather_data(enriched_biosample, schema_field):
                        has_field = True
                        break

                if has_field:
                    field_counts[weather_param] += 1

        # Calculate coverage percentages
        coverage_percentages = {}
        for weather_param in self.WEATHER_FIELDS:
            coverage_percentages[weather_param] = (
                (field_counts[weather_param] / total_samples) * 100
                if total_samples > 0
                else 0
            )

        # Store in tracking structure
        for weather_param, percentage in coverage_percentages.items():
            self.coverage_stats["after"][source][weather_param] = percentage

        return coverage_percentages

    def _has_weather_data(self, biosample: dict[str, Any], field_name: str) -> bool:
        """Check if biosample has data for a specific weather field."""

        # Direct field check
        if field_name in biosample:
            value = biosample[field_name]

            # Handle NMDC QuantityValue format
            if isinstance(value, dict):
                if (
                    "has_numeric_value" in value
                    and value["has_numeric_value"] is not None
                ):
                    return True
                if "has_raw_value" in value and value["has_raw_value"] is not None:
                    return True

            # Handle direct numeric values
            elif (
                isinstance(value, int | float)
                and value is not None
                or isinstance(value, str)
                and value.strip()
            ):
                return True

        return False

    def _calculate_improvements(
        self,
        before_coverage: dict[str, float],
        after_coverage: dict[str, float],
    ) -> dict[str, Any]:
        """Calculate improvement metrics for weather field coverage."""

        improvements = {}

        for weather_param in self.WEATHER_FIELDS:
            before_pct = before_coverage.get(weather_param, 0.0)
            after_pct = after_coverage.get(weather_param, 0.0)

            improvement_pct = after_pct - before_pct
            improvement_ratio = (
                (improvement_pct / before_pct)
                if before_pct > 0
                else float("inf")
                if after_pct > 0
                else 0
            )

            improvements[weather_param] = {
                "before_coverage": before_pct,
                "after_coverage": after_pct,
                "absolute_improvement": improvement_pct,
                "relative_improvement": improvement_ratio,
                "improvement_category": self._categorize_improvement(improvement_pct),
            }

        return improvements

    def _categorize_improvement(self, improvement_pct: float) -> str:
        """Categorize improvement level."""
        if improvement_pct >= 50:
            return "major_improvement"
        elif improvement_pct >= 20:
            return "significant_improvement"
        elif improvement_pct >= 5:
            return "moderate_improvement"
        elif improvement_pct > 0:
            return "minor_improvement"
        else:
            return "no_improvement"

    def _generate_enrichment_summary(self, source: str) -> dict[str, Any]:
        """Generate summary statistics for enrichment results."""

        source_results = [r for r in self.enrichment_results if r["source"] == source]

        if not source_results:
            return {"message": "No enrichment results available"}

        # Temporal quality distribution
        quality_distribution: dict[str, int] = defaultdict(int)
        for result in source_results:
            quality = result["weather_result"].overall_quality.value
            quality_distribution[quality] += 1

        # Provider success rates
        provider_stats: dict[str, int] = defaultdict(int)
        for result in source_results:
            for provider in result["weather_result"].successful_providers:
                provider_stats[provider] += 1

        # Average quality scores
        quality_scores = [
            result["coverage_metrics"]["average_quality_score"]
            for result in source_results
            if result["coverage_metrics"]["average_quality_score"] > 0
        ]

        return {
            "enriched_samples": len(source_results),
            "temporal_quality_distribution": dict(quality_distribution),
            "provider_success_rates": dict(provider_stats),
            "average_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0,
            "enrichment_rate": len(source_results) / len(self.enrichment_results)
            if self.enrichment_results
            else 0,
        }

    def generate_metrics_report(self, analyses: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Generate comprehensive metrics report in tabular format.

        Args:
            analyses: List of analysis results from analyze_biosample_collection

        Returns:
            DataFrame with before/after metrics for all sources and weather fields
        """

        report_data = []

        for analysis in analyses:
            source = analysis["source"]

            for weather_param, improvement_data in analysis["improvements"].items():
                report_data.append(
                    {
                        "source": source.upper(),
                        "weather_parameter": weather_param,
                        "samples": analysis["sample_count"],
                        "before_coverage_%": improvement_data["before_coverage"],
                        "after_coverage_%": improvement_data["after_coverage"],
                        "absolute_improvement_%": improvement_data[
                            "absolute_improvement"
                        ],
                        "improvement_category": improvement_data[
                            "improvement_category"
                        ],
                        "temporal_quality": self._get_primary_temporal_quality(source),
                    }
                )

        return pd.DataFrame(report_data)

    def _get_primary_temporal_quality(self, source: str) -> str:
        """Get the most common temporal quality for a source."""
        source_results = [r for r in self.enrichment_results if r["source"] == source]

        if not source_results:
            return "no_data"

        quality_counts: dict[str, int] = defaultdict(int)
        for result in source_results:
            quality = result["weather_result"].overall_quality.value
            quality_counts[quality] += 1

        return (
            max(quality_counts.keys(), key=lambda k: quality_counts[k])
            if quality_counts
            else "no_data"
        )

    def export_detailed_results(self, output_path: str) -> None:
        """Export detailed enrichment results to CSV for further analysis."""

        detailed_data = []

        for result in self.enrichment_results:
            weather_result = result["weather_result"]
            coverage_metrics = result["coverage_metrics"]

            row = {
                "source": result["source"],
                "biosample_id": result["biosample_id"],
                "lat": weather_result.location["lat"],
                "lon": weather_result.location["lon"],
                "collection_date": weather_result.collection_date,
                "temporal_quality": weather_result.overall_quality.value,
                "enriched_fields": len(coverage_metrics["enriched_fields"]),
                "enrichment_percentage": coverage_metrics["enrichment_percentage"],
                "quality_score": coverage_metrics["average_quality_score"],
                "successful_providers": ",".join(weather_result.successful_providers),
            }

            # Add individual weather parameter flags
            for weather_param in self.WEATHER_FIELDS:
                row[f"has_{weather_param}"] = (
                    weather_param in coverage_metrics["enriched_fields"]
                )

            detailed_data.append(row)

        df = pd.DataFrame(detailed_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Detailed weather enrichment results exported to {output_path}")
