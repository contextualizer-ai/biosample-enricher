"""Command-line interface for biosample enricher."""

import click

from biosample_enricher import __version__
from biosample_enricher.cli_elevation import elevation_cli
from biosample_enricher.cli_forward_geocoding import forward_geocoding
from biosample_enricher.cli_land import land
from biosample_enricher.cli_osm_features import osm_features


def show_version() -> None:
    """Print the biosample-enricher version."""
    print(__version__)


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Biosample Enricher: Infer AI-friendly metadata about biosamples."""


# Add core CLI subcommands (no optional dependencies required)
main.add_command(elevation_cli, name="elevation")
main.add_command(forward_geocoding, name="forward-geocoding")
main.add_command(land, name="land")
main.add_command(osm_features, name="osm-features")

# Note: Metrics evaluation is available via dedicated CLI entry points:
#   - metrics-dashboard (requires optional dependencies: pip install biosample-enricher[metrics])
#   - metrics-markdown (requires optional dependencies: pip install biosample-enricher[metrics])
# This separation avoids importing matplotlib/seaborn for basic package usage.


if __name__ == "__main__":
    main()
