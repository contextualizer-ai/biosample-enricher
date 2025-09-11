"""Command-line interface for biosample enricher."""

import click

from biosample_enricher import __version__
from biosample_enricher.cli_elevation import elevation_cli


def show_version() -> None:
    """Print the biosample-enricher version."""
    print(__version__)


@click.group()
@click.version_option()
def main() -> None:
    """Biosample Enricher: Infer AI-friendly metadata about biosamples."""


# Add elevation CLI as a subcommand
main.add_command(elevation_cli, name="elevation")


if __name__ == "__main__":
    main()
