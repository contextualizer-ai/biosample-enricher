"""Command-line interface for biosample enricher.

The primary CLI command is `get` which wraps get_submission_values() for
retrieving NMDC submission-schema compliant values from geographic coordinates.

Examples:
    # Get climate and elevation data
    biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,annual_temp,elev

    # Show available slots, providers, and strategies
    biosample-enricher info

    # List all slot names (for scripting)
    biosample-enricher slots
"""

import click

from biosample_enricher import __version__
from biosample_enricher.cli_submission_values import submission_values_cli


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Biosample Enricher: Get NMDC submission-schema values for coordinates.

    \b
    Quick Start:
        biosample-enricher get --lat 37.7749 --lon -122.4194 --slots annual_precpt,elev
        biosample-enricher info

    \b
    The primary command is 'get' which retrieves environmental metadata
    from authoritative data sources (elevation, climate, weather, soil, marine)
    and returns it in NMDC submission format.

    \b
    For full documentation:
        https://microbiomedata.github.io/biosample-enricher/
    """


# Add the submission values CLI commands directly to main
# This makes `biosample-enricher get` work instead of `biosample-enricher submission-values get`
for name, cmd in submission_values_cli.commands.items():
    main.add_command(cmd, name=name)


if __name__ == "__main__":
    main()
