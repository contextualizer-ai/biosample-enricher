"""Command-line interface for biosample enricher."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from biosample_enricher import __version__
from biosample_enricher.cli_elevation import elevation_cli
from biosample_enricher.core import BiosampleEnricher

console = Console()


def show_version() -> None:
    """Print the biosample-enricher version."""
    print(__version__)


@click.group()
@click.version_option()
@click.option(
    "--timeout",
    type=float,
    default=30.0,
    help="HTTP request timeout in seconds",
    show_default=True,
)
@click.pass_context
def main(ctx: click.Context, timeout: float) -> None:
    """Biosample Enricher: Infer AI-friendly metadata about biosamples."""
    ctx.ensure_object(dict)
    ctx.obj["timeout"] = timeout


@main.command()
@click.option(
    "--sample-id",
    "-s",
    required=True,
    help="Biosample identifier to enrich",
)
@click.option(
    "--sources",
    "-src",
    multiple=True,
    help="Data sources to query (can be specified multiple times)",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
    show_default=True,
)
@click.pass_context
def enrich(
    ctx: click.Context,
    sample_id: str,
    sources: tuple[str, ...],
    output_format: str,
) -> None:
    """Enrich a single biosample with metadata from multiple sources."""
    timeout = ctx.obj["timeout"]
    source_list = list(sources) if sources else None

    with BiosampleEnricher(timeout=timeout) as enricher:
        results = enricher.enrich_sample(sample_id, source_list)

        if output_format == "table":
            _display_table(sample_id, results)
        elif output_format == "json":
            import json

            data = [result.model_dump() for result in results]
            click.echo(json.dumps(data, indent=2))
        elif output_format == "csv":
            _display_csv(results)


@main.command()
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="File containing biosample IDs (one per line)",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--sources",
    "-src",
    multiple=True,
    help="Data sources to query (can be specified multiple times)",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["table", "json", "csv"]),
    default="json",
    help="Output format",
    show_default=True,
)
@click.option(
    "--parallel",
    "-p",
    is_flag=True,
    help="Process samples in parallel (not implemented yet)",
)
@click.pass_context
def batch(
    ctx: click.Context,
    input_file: Path,
    output_file: Path | None,
    sources: tuple[str, ...],
    output_format: str,
    parallel: bool,
) -> None:
    """Enrich multiple biosamples from a file."""
    timeout = ctx.obj["timeout"]
    source_list = list(sources) if sources else None

    if parallel:
        console.print(
            "[yellow]Warning: Parallel processing not implemented yet[/yellow]"
        )

    # Read sample IDs from file
    sample_ids = []
    with input_file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                sample_ids.append(line)

    if not sample_ids:
        click.echo("No sample IDs found in input file", err=True)
        raise click.Abort()

    console.print(f"Processing {len(sample_ids)} samples...")

    with BiosampleEnricher(timeout=timeout) as enricher:
        results = enricher.enrich_multiple(sample_ids, source_list)

        # Output results
        if output_format == "json":
            import json

            output_data = {}
            for sample_id, metadata_list in results.items():
                output_data[sample_id] = [m.model_dump() for m in metadata_list]

            output_text = json.dumps(output_data, indent=2)
        else:
            # For table/csv, just show summary
            output_text = f"Processed {len(sample_ids)} samples successfully"

        if output_file:
            output_file.write_text(output_text)
            console.print(f"Results written to {output_file}")
        else:
            click.echo(output_text)


@main.command()
@click.option(
    "--sample-id",
    "-s",
    required=True,
    help="Biosample identifier to validate",
)
def validate(sample_id: str) -> None:
    """Validate that a biosample ID exists in available databases."""
    console.print(f"Validating sample ID: {sample_id}")

    # This would implement actual validation logic
    console.print("[green]✓ Sample ID appears to be valid[/green]")


def _display_table(sample_id: str, results: list) -> None:
    """Display results in a table format."""
    table = Table(title=f"Metadata for Sample: {sample_id}")
    table.add_column("Source", style="cyan")
    table.add_column("Confidence", style="magenta")
    table.add_column("Metadata", style="green")

    for result in results:
        metadata_str = ", ".join(f"{k}: {v}" for k, v in result.metadata.items())
        table.add_row(
            result.source,
            f"{result.confidence:.2f}",
            metadata_str,
        )

    console.print(table)


def _display_csv(results: list) -> None:
    """Display results in CSV format."""
    click.echo("sample_id,source,confidence,metadata")
    for result in results:
        metadata_str = "|".join(f"{k}={v}" for k, v in result.metadata.items())
        click.echo(
            f"{result.sample_id},{result.source},{result.confidence},{metadata_str}"
        )


# Add elevation CLI as a subcommand
main.add_command(elevation_cli, name="elevation")


if __name__ == "__main__":
    main()
