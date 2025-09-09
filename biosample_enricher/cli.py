"""Command-line interface for biosample enricher."""

import json
from pathlib import Path

import click
from pydantic import ValidationError

from .core import BiosampleEnricher
from .models import BiosampleMetadata


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--api-timeout", type=float, default=30.0, help="API timeout in seconds")
@click.option("--no-cache", is_flag=True, help="Disable caching")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, api_timeout: float, no_cache: bool) -> None:
    """Biosample Enricher: Infer AI-friendly metadata about biosamples from multiple sources."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["api_timeout"] = api_timeout
    ctx.obj["enable_caching"] = not no_cache


@cli.command()
@click.option(
    "--input-file",
    "-i",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Input JSON file containing biosample metadata",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for enriched metadata (default: stdout)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "jsonl"]),
    default="json",
    help="Output format",
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.pass_context
def enrich(
    ctx: click.Context,
    input_file: Path,
    output_file: Path | None,
    output_format: str,
    pretty: bool,
) -> None:
    """Enrich biosample metadata from input file."""
    verbose = ctx.obj["verbose"]

    if verbose:
        click.echo(f"Reading input from: {input_file}")

    try:
        # Read input data
        with input_file.open() as f:
            input_data = json.load(f)

        # Parse samples
        samples = []
        if isinstance(input_data, list):
            for item in input_data:
                samples.append(BiosampleMetadata(**item))
        elif isinstance(input_data, dict):
            samples.append(BiosampleMetadata(**input_data))
        else:
            raise click.ClickException(
                "Input must be a JSON object or array of objects"
            )

        if verbose:
            click.echo(f"Loaded {len(samples)} sample(s)")

        # Initialize enricher
        enricher = BiosampleEnricher(
            api_timeout=ctx.obj["api_timeout"], enable_caching=ctx.obj["enable_caching"]
        )

        # Enrich samples
        results = enricher.enrich_samples(samples)

        if verbose:
            click.echo(f"Enriched {len(results)} sample(s)")

        # Prepare output
        output_data = []
        for result in results:
            result_dict = {
                "original": result.original_metadata.model_dump(),
                "enriched": result.enriched_metadata.model_dump(),
                "confidence_score": result.confidence_score,
                "sources": result.sources,
                "processing_time": result.processing_time,
            }
            output_data.append(result_dict)

        # Format output
        if output_format == "json":
            if len(output_data) == 1:
                json_output = json.dumps(output_data[0], indent=2 if pretty else None)
            else:
                json_output = json.dumps(output_data, indent=2 if pretty else None)
        else:  # jsonl
            json_output = "\n".join(json.dumps(item) for item in output_data)

        # Write output
        if output_file:
            with output_file.open("w") as f:
                f.write(json_output)
            if verbose:
                click.echo(f"Output written to: {output_file}")
        else:
            click.echo(json_output)

    except ValidationError as e:
        raise click.ClickException(f"Invalid input data: {e}") from e
    except FileNotFoundError as e:
        raise click.ClickException(f"Input file not found: {input_file}") from e
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in input file: {e}") from e
    except Exception as e:
        if verbose:
            raise
        raise click.ClickException(f"Error processing samples: {e}") from e


@cli.command()
@click.option("--sample-id", required=True, help="Sample identifier")
@click.option("--sample-name", help="Sample name")
@click.option("--organism", help="Source organism")
@click.option("--tissue-type", help="Tissue type")
@click.option("--collection-date", help="Collection date")
@click.option("--location", help="Geographic location")
@click.option("--metadata", help="Additional metadata as JSON string")
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for enriched metadata (default: stdout)",
)
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.pass_context
def enrich_single(
    ctx: click.Context,
    sample_id: str,
    sample_name: str | None,
    organism: str | None,
    tissue_type: str | None,
    collection_date: str | None,
    location: str | None,
    metadata: str | None,
    output_file: Path | None,
    pretty: bool,
) -> None:
    """Enrich a single biosample from command-line options."""
    verbose = ctx.obj["verbose"]

    try:
        # Parse additional metadata
        additional_metadata = {}
        if metadata:
            additional_metadata = json.loads(metadata)

        # Create sample
        sample = BiosampleMetadata(
            sample_id=sample_id,
            sample_name=sample_name,
            organism=organism,
            tissue_type=tissue_type,
            collection_date=collection_date,
            location=location,
            metadata=additional_metadata,
        )

        if verbose:
            click.echo(f"Processing sample: {sample_id}")

        # Initialize enricher
        enricher = BiosampleEnricher(
            api_timeout=ctx.obj["api_timeout"], enable_caching=ctx.obj["enable_caching"]
        )

        # Enrich sample
        result = enricher.enrich_sample(sample)

        if verbose:
            click.echo(f"Enrichment completed in {result.processing_time:.2f}s")

        # Prepare output
        result_dict = {
            "original": result.original_metadata.model_dump(),
            "enriched": result.enriched_metadata.model_dump(),
            "confidence_score": result.confidence_score,
            "sources": result.sources,
            "processing_time": result.processing_time,
        }

        # Format output
        json_output = json.dumps(result_dict, indent=2 if pretty else None)

        # Write output
        if output_file:
            with output_file.open("w") as f:
                f.write(json_output)
            if verbose:
                click.echo(f"Output written to: {output_file}")
        else:
            click.echo(json_output)

    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in metadata: {e}") from e
    except ValidationError as e:
        raise click.ClickException(f"Invalid sample data: {e}") from e
    except Exception as e:
        if verbose:
            raise
        raise click.ClickException(f"Error processing sample: {e}") from e


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information about the enricher configuration."""
    click.echo("Biosample Enricher Configuration:")
    click.echo(f"  API Timeout: {ctx.obj['api_timeout']}s")
    click.echo(f"  Caching: {'Enabled' if ctx.obj['enable_caching'] else 'Disabled'}")
    click.echo(f"  Verbose: {'Enabled' if ctx.obj['verbose'] else 'Disabled'}")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
