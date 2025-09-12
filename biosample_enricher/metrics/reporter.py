"""Tabular reporter for biosample enrichment metrics.

Generates CSV files and summary statistics from evaluation results.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)


class MetricsReporter:
    """Generates tabular reports from evaluation results."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize reporter with output directory.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir or Path("data/metrics")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary_table(
        self, evaluations: list[dict[str, Any]], exclude_host_associated: bool = False
    ) -> pd.DataFrame:
        """Generate overall coverage summary table.

        Args:
            evaluations: List of evaluation results
            exclude_host_associated: Whether to exclude host-associated samples

        Returns:
            DataFrame with coverage summary by source and data type
        """
        # Optionally filter out host-associated samples
        if exclude_host_associated:
            evaluations = [
                e for e in evaluations if not e.get("is_host_associated", False)
            ]
            logger.info(
                f"Excluding host-associated samples, {len(evaluations)} samples remaining"
            )

        # Separate by source
        nmdc_evals = [e for e in evaluations if e.get("source") == "nmdc"]
        gold_evals = [e for e in evaluations if e.get("source") == "gold"]

        # Calculate metrics for each data type
        metrics = []

        # Elevation metrics
        for source_name, source_evals in [("NMDC", nmdc_evals), ("GOLD", gold_evals)]:
            if not source_evals:
                continue

            # Elevation coverage
            elev_before = sum(
                1 for e in source_evals if e.get("elevation", {}).get("before", False)
            )
            elev_after = sum(
                1 for e in source_evals if e.get("elevation", {}).get("after", False)
            )
            total = len(source_evals)

            metrics.append(
                {
                    "source": source_name,
                    "data_type": "Elevation",
                    "samples": total,
                    "before": round(100 * elev_before / total, 1) if total > 0 else 0,
                    "after": round(100 * elev_after / total, 1) if total > 0 else 0,
                    "improvement": round(100 * (elev_after - elev_before) / total, 1)
                    if total > 0
                    else 0,
                }
            )

            # Place name coverage (overall)
            place_before = sum(
                1 for e in source_evals if e.get("place_name", {}).get("before", False)
            )
            place_after = sum(
                1 for e in source_evals if e.get("place_name", {}).get("after", False)
            )

            metrics.append(
                {
                    "source": source_name,
                    "data_type": "Place Name",
                    "samples": total,
                    "before": round(100 * place_before / total, 1) if total > 0 else 0,
                    "after": round(100 * place_after / total, 1) if total > 0 else 0,
                    "improvement": round(100 * (place_after - place_before) / total, 1)
                    if total > 0
                    else 0,
                }
            )

            # Place name components
            for component in ["country", "state", "locality"]:
                comp_before = sum(
                    1
                    for e in source_evals
                    if e.get("place_name", {})
                    .get("component_coverage", {})
                    .get(component, {})
                    .get("before", False)
                )
                comp_after = sum(
                    1
                    for e in source_evals
                    if e.get("place_name", {})
                    .get("component_coverage", {})
                    .get(component, {})
                    .get("after", False)
                )

                metrics.append(
                    {
                        "source": source_name,
                        "data_type": f"Place Name - {component.title()}",
                        "samples": total,
                        "before": round(100 * comp_before / total, 1)
                        if total > 0
                        else 0,
                        "after": round(100 * comp_after / total, 1) if total > 0 else 0,
                        "improvement": round(
                            100 * (comp_after - comp_before) / total, 1
                        )
                        if total > 0
                        else 0,
                    }
                )

            # Weather coverage (overall)
            weather_before_count = sum(
                e.get("weather", {}).get("before_count", 0) for e in source_evals
            )
            weather_after_count = sum(
                e.get("weather", {}).get("after_count", 0) for e in source_evals
            )
            weather_total_possible = sum(
                e.get("weather", {}).get("total_possible", 7) for e in source_evals
            )

            if weather_total_possible > 0:
                metrics.append(
                    {
                        "source": source_name,
                        "data_type": "Weather",
                        "samples": total,
                        "before": round(
                            100 * weather_before_count / weather_total_possible, 1
                        ),
                        "after": round(
                            100 * weather_after_count / weather_total_possible, 1
                        ),
                        "improvement": round(
                            100
                            * (weather_after_count - weather_before_count)
                            / weather_total_possible,
                            1,
                        ),
                    }
                )

            # Individual weather parameters
            weather_fields = [
                "temperature",
                "wind_speed",
                "wind_direction",
                "humidity",
                "solar_radiation",
                "precipitation",
                "pressure",
                "chlorophyll",
            ]

            for weather_param in weather_fields:
                param_before = sum(
                    1
                    for e in source_evals
                    if e.get("weather", {}).get("before", {}).get(weather_param, False)
                )
                param_after = sum(
                    1
                    for e in source_evals
                    if e.get("weather", {}).get("after", {}).get(weather_param, False)
                )

                metrics.append(
                    {
                        "source": source_name,
                        "data_type": f"Weather - {weather_param.replace('_', ' ').title()}",
                        "samples": total,
                        "before": round(100 * param_before / total, 1)
                        if total > 0
                        else 0,
                        "after": round(100 * param_after / total, 1)
                        if total > 0
                        else 0,
                        "improvement": round(
                            100 * (param_after - param_before) / total, 1
                        )
                        if total > 0
                        else 0,
                    }
                )

            # Marine coverage (overall)
            marine_before_count = sum(
                e.get("marine", {}).get("before_count", 0) for e in source_evals
            )
            marine_after_count = sum(
                e.get("marine", {}).get("after_count", 0) for e in source_evals
            )
            marine_total_possible = sum(
                e.get("marine", {}).get("total_possible", 7) for e in source_evals
            )

            if marine_total_possible > 0:
                metrics.append(
                    {
                        "source": source_name,
                        "data_type": "Marine",
                        "samples": total,
                        "before": round(
                            100 * marine_before_count / marine_total_possible, 1
                        ),
                        "after": round(
                            100 * marine_after_count / marine_total_possible, 1
                        ),
                        "improvement": round(
                            100
                            * (marine_after_count - marine_before_count)
                            / marine_total_possible,
                            1,
                        ),
                    }
                )

            # Individual marine parameters
            marine_fields = [
                "sea_surface_temperature",
                "bathymetry",
                "chlorophyll_a",
                "salinity",
                "dissolved_oxygen",
                "ph",
                "wave_height",
            ]

            for marine_param in marine_fields:
                param_before = sum(
                    1
                    for e in source_evals
                    if e.get("marine", {}).get("before", {}).get(marine_param, False)
                )
                param_after = sum(
                    1
                    for e in source_evals
                    if e.get("marine", {}).get("after", {}).get(marine_param, False)
                )

                metrics.append(
                    {
                        "source": source_name,
                        "data_type": f"Marine - {marine_param.replace('_', ' ').title()}",
                        "samples": total,
                        "before": round(100 * param_before / total, 1)
                        if total > 0
                        else 0,
                        "after": round(100 * param_after / total, 1)
                        if total > 0
                        else 0,
                        "improvement": round(
                            100 * (param_after - param_before) / total, 1
                        )
                        if total > 0
                        else 0,
                    }
                )

        df = pd.DataFrame(metrics)

        # Add formatted improvement column
        if not df.empty:
            df["improvement_fmt"] = df["improvement"].apply(
                lambda x: f"+{x}%" if x > 0 else f"{x}%"
            )

        return df

    def generate_regional_table(
        self, evaluations: list[dict[str, Any]]
    ) -> pd.DataFrame:
        """Generate coverage table by geographic region.

        Args:
            evaluations: List of evaluation results

        Returns:
            DataFrame with coverage by region
        """
        regional_data = []

        # Group by source and region
        for source in ["nmdc", "gold"]:
            source_evals = [e for e in evaluations if e.get("source") == source]

            # Group by region
            regions: dict[str, list[dict[str, Any]]] = {}
            for eval_result in source_evals:
                region = eval_result.get("classification", {}).get("region", "Unknown")
                if region not in regions:
                    regions[region] = []
                regions[region].append(eval_result)

            # Calculate metrics for each region
            for region, region_evals in regions.items():
                if not region_evals:
                    continue

                total = len(region_evals)

                # Has coordinates
                has_coords = sum(
                    1
                    for e in region_evals
                    if e.get("classification", {}).get("has_coordinates", False)
                )

                # Elevation
                elev_before = sum(
                    1
                    for e in region_evals
                    if e.get("elevation", {}).get("before", False)
                )
                elev_after = sum(
                    1
                    for e in region_evals
                    if e.get("elevation", {}).get("after", False)
                )

                # Place name
                place_before = sum(
                    1
                    for e in region_evals
                    if e.get("place_name", {}).get("before", False)
                )
                place_after = sum(
                    1
                    for e in region_evals
                    if e.get("place_name", {}).get("after", False)
                )

                regional_data.append(
                    {
                        "source": source.upper(),
                        "region": region,
                        "samples": total,
                        "has_coordinates_%": round(100 * has_coords / total, 1)
                        if total > 0
                        else 0,
                        "elevation_before_%": round(100 * elev_before / total, 1)
                        if total > 0
                        else 0,
                        "elevation_after_%": round(100 * elev_after / total, 1)
                        if total > 0
                        else 0,
                        "place_name_before_%": round(100 * place_before / total, 1)
                        if total > 0
                        else 0,
                        "place_name_after_%": round(100 * place_after / total, 1)
                        if total > 0
                        else 0,
                    }
                )

        return pd.DataFrame(regional_data)

    def generate_detailed_samples(
        self, evaluations: list[dict[str, Any]], limit: int = 100
    ) -> pd.DataFrame:
        """Generate detailed per-sample results.

        Args:
            evaluations: List of evaluation results
            limit: Maximum number of samples to include

        Returns:
            DataFrame with detailed sample-level data
        """
        detailed = []

        for eval_result in evaluations[:limit]:
            detailed.append(
                {
                    "sample_id": eval_result.get("sample_id"),
                    "source": eval_result.get("source"),
                    "region": eval_result.get("classification", {}).get("region"),
                    "is_us": eval_result.get("classification", {}).get(
                        "is_us_territory"
                    ),
                    "is_ocean": eval_result.get("classification", {}).get("is_ocean"),
                    # Elevation
                    "elev_before": eval_result.get("elevation", {}).get("before_value"),
                    "elev_after": eval_result.get("elevation", {}).get("after_value"),
                    "elev_provider": eval_result.get("elevation", {}).get("provider"),
                    # Place name
                    "place_before": eval_result.get("place_name", {}).get(
                        "before_flat"
                    ),
                    "place_after": eval_result.get("place_name", {}).get("after_flat"),
                    "place_providers": ", ".join(
                        eval_result.get("place_name", {}).get("providers", [])
                    ),
                    # Marine
                    "marine_before_count": eval_result.get("marine", {}).get(
                        "before_count", 0
                    ),
                    "marine_after_count": eval_result.get("marine", {}).get(
                        "after_count", 0
                    ),
                    "marine_improvement": eval_result.get("marine", {}).get(
                        "improved", False
                    ),
                    "marine_providers": ", ".join(
                        eval_result.get("marine", {}).get("providers", [])
                    ),
                    "marine_quality": eval_result.get("marine", {}).get("data_quality"),
                    # Weather
                    "weather_before_count": eval_result.get("weather", {}).get(
                        "before_count", 0
                    ),
                    "weather_after_count": eval_result.get("weather", {}).get(
                        "after_count", 0
                    ),
                    "weather_improvement": eval_result.get("weather", {}).get(
                        "improved", False
                    ),
                    "weather_providers": ", ".join(
                        eval_result.get("weather", {}).get("providers", [])
                    ),
                    "weather_quality": eval_result.get("weather", {}).get(
                        "data_quality"
                    ),
                }
            )

        return pd.DataFrame(detailed)

    def save_all_reports(
        self, evaluations: list[dict[str, Any]], prefix: str = "metrics"
    ) -> dict[str, Path]:
        """Save all report tables to CSV files.

        Args:
            evaluations: List of evaluation results
            prefix: Filename prefix

        Returns:
            Dictionary of report names to file paths
        """
        files = {}

        # Summary table
        summary_df = self.generate_summary_table(evaluations)
        summary_path = self.output_dir / f"{prefix}_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        files["summary"] = summary_path
        logger.info(f"Saved summary table to {summary_path}")

        # Regional table
        regional_df = self.generate_regional_table(evaluations)
        regional_path = self.output_dir / f"{prefix}_by_region.csv"
        regional_df.to_csv(regional_path, index=False)
        files["regional"] = regional_path
        logger.info(f"Saved regional table to {regional_path}")

        # Detailed samples
        detailed_df = self.generate_detailed_samples(evaluations)
        detailed_path = self.output_dir / f"{prefix}_samples.csv"
        detailed_df.to_csv(detailed_path, index=False)
        files["samples"] = detailed_path
        logger.info(f"Saved sample details to {detailed_path}")

        # Print summary to console
        self.print_summary(summary_df)

        return files

    def print_summary(self, summary_df: pd.DataFrame) -> None:
        """Print summary table to console.

        Args:
            summary_df: Summary DataFrame
        """
        print("\n" + "=" * 80)
        print("BIOSAMPLE ENRICHMENT COVERAGE METRICS")
        print("=" * 80)

        if summary_df.empty:
            print("No data available")
            return

        # Format for console display
        display_df = summary_df[
            ["source", "data_type", "samples", "before", "after", "improvement_fmt"]
        ].copy()

        display_df.columns = [
            "Source",
            "Data Type",
            "Samples",
            "Before %",
            "After %",
            "Improvement",
        ]

        print("\n" + display_df.to_string(index=False))
        print("=" * 80)

        # Calculate overall statistics
        for source in summary_df["source"].unique():
            source_data = summary_df[summary_df["source"] == source]
            avg_before = source_data["before"].mean()
            avg_after = source_data["after"].mean()
            avg_improvement = source_data["improvement"].mean()

            print(f"\n{source} Overall:")
            print(f"  Average Before: {avg_before:.1f}%")
            print(f"  Average After: {avg_after:.1f}%")
            print(f"  Average Improvement: +{avg_improvement:.1f}%")

        print()
