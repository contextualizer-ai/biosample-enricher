"""Visualization module for biosample enrichment metrics.

Creates bar charts and other visualizations from evaluation results.
"""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from biosample_enricher.logging_config import get_logger

logger = get_logger(__name__)

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 100
plt.rcParams["savefig.dpi"] = 150


class MetricsVisualizer:
    """Creates visualizations from metrics evaluation results."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize visualizer with output directory.

        Args:
            output_dir: Directory for saving plots
        """
        self.output_dir = output_dir or Path("data/metrics")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_source_datatype_coverage(
        self, summary_df: pd.DataFrame, save_path: Path | None = None
    ) -> plt.Figure:
        """Create grouped bar chart for source × data type coverage.

        Args:
            summary_df: DataFrame with columns: source, data_type, before, after
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure
        """
        # Prepare data for plotting
        data_types = summary_df["data_type"].unique()
        sources = summary_df["source"].unique()

        # Set up the plot
        fig, ax = plt.subplots(figsize=(14, 8))

        # Define bar positions
        x = np.arange(len(data_types))
        width = 0.2

        # Color scheme
        colors = {
            "NMDC": "#1f77b4",  # Blue
            "GOLD": "#ff7f0e",  # Orange
        }

        # Create bars for each source × timing combination

        for i, source in enumerate(sources):
            source_data = summary_df[summary_df["source"] == source]

            # Align data with data_types order
            before_values = []
            after_values = []
            for dt in data_types:
                dt_data = source_data[source_data["data_type"] == dt]
                if not dt_data.empty:
                    before_values.append(dt_data["before"].values[0])
                    after_values.append(dt_data["after"].values[0])
                else:
                    before_values.append(0)
                    after_values.append(0)

            # Create bars
            offset = (i - len(sources) / 2 + 0.5) * width * 2

            # Before bars (lighter/transparent)
            bars_before = ax.bar(
                x + offset - width / 2,
                before_values,
                width,
                label=f"{source} Before",
                color=colors.get(source, "#333333"),
                alpha=0.4,
            )

            # After bars (solid)
            bars_after = ax.bar(
                x + offset + width / 2,
                after_values,
                width,
                label=f"{source} After",
                color=colors.get(source, "#333333"),
            )

            # Add value labels on bars
            for bar in bars_before:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(
                        f"{height:.0f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

            for bar in bars_after:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(
                        f"{height:.0f}%",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        # Customize plot
        ax.set_xlabel("Data Type", fontsize=12, fontweight="bold")
        ax.set_ylabel("Coverage (%)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Biosample Data Coverage: Before and After Enrichment",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xticks(x)
        ax.set_xticklabels(data_types, rotation=45, ha="right")
        ax.legend(loc="upper left", ncol=4, frameon=True, fancybox=True)
        ax.grid(axis="y", alpha=0.3)
        ax.set_ylim(0, 105)

        plt.tight_layout()

        # Save if path provided
        if save_path:
            fig.savefig(save_path, bbox_inches="tight")
            logger.info(f"Saved coverage plot to {save_path}")

        return fig

    def plot_improvement_bars(
        self, summary_df: pd.DataFrame, save_path: Path | None = None
    ) -> plt.Figure:
        """Create bar chart showing improvement percentages.

        Args:
            summary_df: DataFrame with columns: source, data_type, improvement
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure
        """
        # Pivot data for grouped bar plot
        pivot_df = summary_df.pivot(
            index="data_type", columns="source", values="improvement"
        )

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        # Create grouped bar plot
        pivot_df.plot(kind="bar", ax=ax, width=0.7, color=["#1f77b4", "#ff7f0e"])

        # Customize
        ax.set_xlabel("Data Type", fontsize=12, fontweight="bold")
        ax.set_ylabel("Coverage Improvement (%)", fontsize=12, fontweight="bold")
        ax.set_title(
            "Enrichment Impact by Source and Data Type", fontsize=14, fontweight="bold"
        )
        ax.legend(title="Source", title_fontsize=10, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

        # Rotate x labels
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

        # Add value labels on bars
        try:
            for container in ax.containers:
                ax.bar_label(container, fmt="%.1f%%", padding=3, fontsize=8)  # type: ignore[arg-type]
        except (AttributeError, TypeError):
            # Skip bar labeling if container type is incompatible
            pass

        plt.tight_layout()

        # Save if path provided
        if save_path:
            fig.savefig(save_path, bbox_inches="tight")
            logger.info(f"Saved improvement plot to {save_path}")

        return fig

    def plot_regional_comparison(
        self, regional_df: pd.DataFrame, save_path: Path | None = None
    ) -> plt.Figure:
        """Create regional comparison plot.

        Args:
            regional_df: DataFrame with regional metrics
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure
        """
        # Filter out unknown regions and sort by sample count
        plot_df = regional_df[regional_df["region"] != "Unknown"].copy()
        plot_df = plot_df.sort_values("samples", ascending=False)

        # Create subplots for elevation and place name
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Elevation subplot
        ax1 = axes[0]
        regions = plot_df["region"].unique()
        x = np.arange(len(regions))
        width = 0.35

        for i, source in enumerate(plot_df["source"].unique()):
            source_data = plot_df[plot_df["source"] == source]

            # Align data with regions order
            before_values = []
            after_values = []
            for region in regions:
                region_data = source_data[source_data["region"] == region]
                if not region_data.empty:
                    before_values.append(region_data["elevation_before_%"].values[0])
                    after_values.append(region_data["elevation_after_%"].values[0])
                else:
                    before_values.append(0)
                    after_values.append(0)

            offset = (i - 0.5) * width
            ax1.bar(
                x + offset - width / 4,
                before_values,
                width / 2,
                label=f"{source} Before",
                alpha=0.6,
            )
            ax1.bar(
                x + offset + width / 4, after_values, width / 2, label=f"{source} After"
            )

        ax1.set_title("Elevation Coverage by Region", fontweight="bold")
        ax1.set_xlabel("Region")
        ax1.set_ylabel("Coverage (%)")
        ax1.set_xticks(x)
        ax1.set_xticklabels(regions, rotation=45, ha="right")
        ax1.legend(fontsize=8)
        ax1.grid(axis="y", alpha=0.3)

        # Place name subplot
        ax2 = axes[1]

        for i, source in enumerate(plot_df["source"].unique()):
            source_data = plot_df[plot_df["source"] == source]

            # Align data with regions order
            before_values = []
            after_values = []
            for region in regions:
                region_data = source_data[source_data["region"] == region]
                if not region_data.empty:
                    before_values.append(region_data["place_name_before_%"].values[0])
                    after_values.append(region_data["place_name_after_%"].values[0])
                else:
                    before_values.append(0)
                    after_values.append(0)

            offset = (i - 0.5) * width
            ax2.bar(
                x + offset - width / 4,
                before_values,
                width / 2,
                label=f"{source} Before",
                alpha=0.6,
            )
            ax2.bar(
                x + offset + width / 4, after_values, width / 2, label=f"{source} After"
            )

        ax2.set_title("Place Name Coverage by Region", fontweight="bold")
        ax2.set_xlabel("Region")
        ax2.set_ylabel("Coverage (%)")
        ax2.set_xticks(x)
        ax2.set_xticklabels(regions, rotation=45, ha="right")
        ax2.legend(fontsize=8)
        ax2.grid(axis="y", alpha=0.3)

        plt.suptitle("Regional Coverage Analysis", fontsize=14, fontweight="bold")
        plt.tight_layout()

        # Save if path provided
        if save_path:
            fig.savefig(save_path, bbox_inches="tight")
            logger.info(f"Saved regional plot to {save_path}")

        return fig

    def plot_host_association_breakdown(
        self, evaluations: list[dict[str, Any]], save_path: Path | None = None
    ) -> plt.Figure:
        """Create pie charts showing host-associated vs environmental samples.

        Args:
            evaluations: List of evaluation results
            save_path: Optional path to save the figure

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Count host-associated by source
        for i, source in enumerate(["nmdc", "gold"]):
            source_evals = [e for e in evaluations if e.get("source") == source]

            if not source_evals:
                continue

            host_associated = sum(
                1 for e in source_evals if e.get("is_host_associated")
            )
            environmental = len(source_evals) - host_associated

            # Create pie chart
            ax = axes[i]
            labels = ["Environmental", "Host-Associated"]
            sizes = [environmental, host_associated]
            colors = ["#2ecc71", "#e74c3c"]

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90
            )

            ax.set_title(
                f"{source.upper()} Samples\n(n={len(source_evals)})", fontweight="bold"
            )

            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_fontweight("bold")
                autotext.set_color("white")

        plt.suptitle("Sample Type Distribution", fontsize=14, fontweight="bold")
        plt.tight_layout()

        # Save if path provided
        if save_path:
            fig.savefig(save_path, bbox_inches="tight")
            logger.info(f"Saved host association plot to {save_path}")

        return fig

    def create_all_visualizations(
        self,
        evaluations: list[dict[str, Any]],
        summary_df: pd.DataFrame,
        regional_df: pd.DataFrame,
        prefix: str = "metrics",
    ) -> dict[str, Path]:
        """Create all visualization plots.

        Args:
            evaluations: List of evaluation results
            summary_df: Summary metrics DataFrame
            regional_df: Regional metrics DataFrame
            prefix: Filename prefix

        Returns:
            Dictionary of plot names to file paths
        """
        plots = {}

        # Main coverage plot
        coverage_path = self.output_dir / f"{prefix}_coverage.png"
        self.plot_source_datatype_coverage(summary_df, coverage_path)
        plots["coverage"] = coverage_path

        # Improvement plot
        improvement_path = self.output_dir / f"{prefix}_improvement.png"
        self.plot_improvement_bars(summary_df, improvement_path)
        plots["improvement"] = improvement_path

        # Regional plot
        if not regional_df.empty:
            regional_path = self.output_dir / f"{prefix}_regional.png"
            self.plot_regional_comparison(regional_df, regional_path)
            plots["regional"] = regional_path

        # Host association plot
        host_path = self.output_dir / f"{prefix}_host_association.png"
        self.plot_host_association_breakdown(evaluations, host_path)
        plots["host_association"] = host_path

        logger.info(f"Created {len(plots)} visualization plots")

        return plots
