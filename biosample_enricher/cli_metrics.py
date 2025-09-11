"""CLI commands for biosample enrichment metrics evaluation."""

from pathlib import Path

import click

from biosample_enricher.logging_config import get_logger, setup_logging
from biosample_enricher.metrics import (
    BiosampleMetricsFetcher,
    CoverageEvaluator,
    MetricsReporter,
    MetricsVisualizer,
)

logger = get_logger(__name__)


@click.group()
def metrics() -> None:
    """Evaluate enrichment coverage metrics."""
    pass


@metrics.command()
@click.option(
    "--nmdc-samples",
    type=int,
    default=100,
    help="Number of random NMDC samples to evaluate",
)
@click.option(
    "--gold-samples",
    type=int,
    default=100,
    help="Number of random GOLD samples to evaluate",
)
@click.option(
    "--exclude-host",
    is_flag=True,
    help="Exclude host-associated samples from metrics",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="data/metrics",
    help="Directory for output files",
)
@click.option(
    "--nmdc-connection",
    envvar="NMDC_MONGO_CONNECTION",
    help="MongoDB connection string for NMDC",
)
@click.option(
    "--gold-connection",
    envvar="GOLD_MONGO_CONNECTION",
    help="MongoDB connection string for GOLD",
)
@click.option(
    "--create-plots",
    is_flag=True,
    default=True,
    help="Create visualization plots",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--debug-samples",
    is_flag=True,
    help="Show detailed sample data at each processing stage",
)
@click.option(
    "--workspace-dir",
    type=click.Path(path_type=Path),
    default="data/workspace",
    help="Directory for detailed debug files (raw docs, API responses, etc.)",
)
def evaluate(
    nmdc_samples: int,
    gold_samples: int,
    exclude_host: bool,
    output_dir: Path,
    nmdc_connection: str | None,
    gold_connection: str | None,
    create_plots: bool,
    verbose: bool,
    debug_samples: bool,
    workspace_dir: Path,
) -> None:
    """Evaluate enrichment coverage metrics for random samples.

    This command:
    1. Fetches random samples from NMDC and GOLD databases
    2. Runs enrichment (elevation and reverse geocoding)
    3. Compares coverage before and after enrichment
    4. Generates tabular reports and visualizations
    """
    # Setup logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    logger.info("Starting metrics evaluation")
    logger.info(f"NMDC samples: {nmdc_samples}, GOLD samples: {gold_samples}")

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create workspace directory if debug is enabled
    if debug_samples:
        workspace_dir = Path(workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Debug workspace: {workspace_dir}")

    # Initialize components
    fetcher = BiosampleMetricsFetcher(
        nmdc_connection_string=nmdc_connection,
        gold_connection_string=gold_connection,
    )

    evaluator = CoverageEvaluator()
    reporter = MetricsReporter(output_dir)

    all_evaluations = []

    # Fetch and evaluate NMDC samples
    if nmdc_samples > 0:
        logger.info(f"Fetching {nmdc_samples} random NMDC samples...")
        try:
            raw_docs, locations = fetcher.fetch_nmdc_samples(nmdc_samples)

            if locations:
                logger.info(f"Evaluating {len(locations)} NMDC samples...")

                # Debug sample data if requested
                if debug_samples:
                    import json

                    # Write detailed debug files to workspace
                    nmdc_workspace = workspace_dir / "nmdc"
                    nmdc_workspace.mkdir(exist_ok=True)

                    for i, (raw_doc, location) in enumerate(
                        zip(raw_docs, locations, strict=False)
                    ):
                        sample_id = (
                            location.sample_id.replace(":", "_")
                            if location.sample_id
                            else "unknown"
                        )

                        # Write raw document
                        with open(nmdc_workspace / f"{sample_id}_raw.json", "w") as f:
                            json.dump(raw_doc, f, indent=2, default=str)

                        # Write normalized location
                        with open(
                            nmdc_workspace / f"{sample_id}_normalized.json", "w"
                        ) as f:
                            json.dump(location.model_dump(), f, indent=2, default=str)

                        logger.info(f"\n=== NMDC SAMPLE {i + 1} DEBUG ===")
                        logger.info(f"Sample ID: {location.sample_id}")
                        logger.info(
                            f"Raw doc saved: {nmdc_workspace / f'{sample_id}_raw.json'}"
                        )
                        logger.info(
                            f"Normalized saved: {nmdc_workspace / f'{sample_id}_normalized.json'}"
                        )
                        logger.info("=" * 50)

                samples = list(zip(raw_docs, locations, strict=False))
                nmdc_results = evaluator.evaluate_batch(samples, "nmdc")

                # Debug evaluation results if requested
                if debug_samples:
                    for i, result in enumerate(nmdc_results):
                        sample_id = result["sample_id"].replace(":", "_")

                        # Write evaluation result
                        with open(
                            nmdc_workspace / f"{sample_id}_evaluation.json", "w"
                        ) as f:
                            json.dump(result, f, indent=2, default=str)

                        logger.info(f"\n=== NMDC EVALUATION RESULT {i + 1} ===")
                        logger.info(f"Sample ID: {result['sample_id']}")
                        logger.info(
                            f"Evaluation saved: {nmdc_workspace / f'{sample_id}_evaluation.json'}"
                        )
                        logger.info("=" * 50)

                all_evaluations.extend(nmdc_results)

                # Report host-associated statistics
                host_count = sum(1 for r in nmdc_results if r.get("is_host_associated"))
                logger.info(
                    f"NMDC: {host_count}/{len(nmdc_results)} samples are host-associated"
                )
            else:
                logger.warning("No NMDC samples retrieved")

        except Exception as e:
            logger.error(f"Error processing NMDC samples: {e}")

    # Fetch and evaluate GOLD samples
    if gold_samples > 0:
        logger.info(f"Fetching {gold_samples} random GOLD samples...")
        try:
            raw_docs, locations = fetcher.fetch_gold_samples(gold_samples)

            if locations:
                logger.info(f"Evaluating {len(locations)} GOLD samples...")

                # Debug sample data if requested
                if debug_samples:
                    # Write detailed debug files to workspace
                    gold_workspace = workspace_dir / "gold"
                    gold_workspace.mkdir(exist_ok=True)

                    for i, (raw_doc, location) in enumerate(
                        zip(raw_docs, locations, strict=False)
                    ):
                        sample_id = (
                            location.sample_id.replace(":", "_").replace("/", "_")
                            if location.sample_id
                            else "unknown"
                        )

                        # Write raw document
                        with open(gold_workspace / f"{sample_id}_raw.json", "w") as f:
                            json.dump(raw_doc, f, indent=2, default=str)

                        # Write normalized location
                        with open(
                            gold_workspace / f"{sample_id}_normalized.json", "w"
                        ) as f:
                            json.dump(location.model_dump(), f, indent=2, default=str)

                        logger.info(f"\n=== GOLD SAMPLE {i + 1} DEBUG ===")
                        logger.info(f"Sample ID: {location.sample_id}")
                        logger.info(
                            f"Raw doc saved: {gold_workspace / f'{sample_id}_raw.json'}"
                        )
                        logger.info(
                            f"Normalized saved: {gold_workspace / f'{sample_id}_normalized.json'}"
                        )
                        logger.info("=" * 50)

                samples = list(zip(raw_docs, locations, strict=False))
                gold_results = evaluator.evaluate_batch(samples, "gold")

                # Debug evaluation results if requested
                if debug_samples:
                    for i, result in enumerate(gold_results):
                        sample_id = (
                            result["sample_id"].replace(":", "_").replace("/", "_")
                        )

                        # Write evaluation result
                        with open(
                            gold_workspace / f"{sample_id}_evaluation.json", "w"
                        ) as f:
                            json.dump(result, f, indent=2, default=str)

                        logger.info(f"\n=== GOLD EVALUATION RESULT {i + 1} ===")
                        logger.info(f"Sample ID: {result['sample_id']}")
                        logger.info(
                            f"Evaluation saved: {gold_workspace / f'{sample_id}_evaluation.json'}"
                        )
                        logger.info("=" * 50)

                all_evaluations.extend(gold_results)

                # Report host-associated statistics
                host_count = sum(1 for r in gold_results if r.get("is_host_associated"))
                logger.info(
                    f"GOLD: {host_count}/{len(gold_results)} samples are host-associated"
                )
            else:
                logger.warning("No GOLD samples retrieved")

        except Exception as e:
            logger.error(f"Error processing GOLD samples: {e}")

    if not all_evaluations:
        logger.error("No samples were evaluated")
        return

    # Generate reports
    logger.info("Generating reports...")

    # Summary table
    summary_df = reporter.generate_summary_table(all_evaluations, exclude_host)

    # Regional table
    regional_df = reporter.generate_regional_table(all_evaluations)

    # Detailed samples
    reporter.generate_detailed_samples(all_evaluations)

    # Save all reports
    report_files = reporter.save_all_reports(all_evaluations, prefix="metrics")

    # Create visualizations
    if create_plots:
        logger.info("Creating visualization plots...")
        visualizer = MetricsVisualizer(output_dir)
        plot_files = visualizer.create_all_visualizations(
            all_evaluations, summary_df, regional_df, prefix="metrics"
        )

        logger.info(f"Created {len(plot_files)} plots")

    # Print summary
    click.echo("\n" + "=" * 80)
    click.echo("METRICS EVALUATION COMPLETE")
    click.echo("=" * 80)
    click.echo(f"Total samples evaluated: {len(all_evaluations)}")
    click.echo(f"Output directory: {output_dir}")
    click.echo("\nGenerated files:")
    for name, path in report_files.items():
        click.echo(f"  - {name}: {path.name}")
    if create_plots:
        for name, path in plot_files.items():
            click.echo(f"  - {name}: {path.name}")
    click.echo("=" * 80)


@metrics.command()
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="data/metrics",
    help="Directory for output files",
)
def visualize(csv_file: Path, output_dir: Path) -> None:
    """Create visualizations from existing metrics CSV file.

    CSV_FILE: Path to metrics summary CSV file
    """
    import pandas as pd

    setup_logging()

    # Load CSV
    df = pd.read_csv(csv_file)

    # Create visualizer
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    visualizer = MetricsVisualizer(output_dir)

    # Create main coverage plot
    fig = visualizer.plot_source_datatype_coverage(df)
    output_path = output_dir / "coverage_plot.png"
    fig.savefig(output_path, bbox_inches="tight")

    click.echo(f"Created visualization: {output_path}")


@metrics.command()
@click.option(
    "--nmdc-connection",
    envvar="NMDC_MONGO_CONNECTION",
    help="MongoDB connection string for NMDC",
)
@click.option(
    "--gold-connection",
    envvar="GOLD_MONGO_CONNECTION",
    help="MongoDB connection string for GOLD",
)
def test_connection(nmdc_connection: str | None, gold_connection: str | None) -> None:
    """Test database connections."""
    setup_logging()

    fetcher = BiosampleMetricsFetcher(
        nmdc_connection_string=nmdc_connection,
        gold_connection_string=gold_connection,
    )

    # Test NMDC
    if nmdc_connection:
        click.echo("Testing NMDC connection...")
        try:
            if fetcher.nmdc_fetcher.connect():
                count = fetcher.nmdc_fetcher.count_total_samples()
                click.echo(f"✓ NMDC connection successful. Total samples: {count}")
                fetcher.nmdc_fetcher.disconnect()
            else:
                click.echo("✗ NMDC connection failed")
        except Exception as e:
            click.echo(f"✗ NMDC connection error: {e}")
    else:
        click.echo("No NMDC connection string provided")

    # Test GOLD
    if gold_connection:
        click.echo("Testing GOLD connection...")
        try:
            if fetcher.gold_fetcher.connect():
                count = fetcher.gold_fetcher.count_total_samples()
                click.echo(f"✓ GOLD connection successful. Total samples: {count}")
                fetcher.gold_fetcher.disconnect()
            else:
                click.echo("✗ GOLD connection failed")
        except Exception as e:
            click.echo(f"✗ GOLD connection error: {e}")
    else:
        click.echo("No GOLD connection string provided")


if __name__ == "__main__":
    metrics()
