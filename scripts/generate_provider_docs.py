#!/usr/bin/env python3
"""
Generate markdown documentation from provider metadata.

This script reads config/provider_metadata.yaml and generates comprehensive
markdown documentation with comparison tables and detailed provider profiles.

Usage:
    python scripts/generate_provider_docs.py [--output docs/PROVIDERS.md]
"""

import argparse
from pathlib import Path
from typing import Any

import yaml


def load_provider_metadata(config_path: Path) -> dict[str, Any]:
    """Load provider metadata from YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data["providers"]


def generate_overview_table(providers: dict[str, Any]) -> str:
    """Generate overview comparison table."""
    lines = []
    lines.append("## Provider Overview")
    lines.append("")
    lines.append("| Provider | Domain | Coverage | API Key | Cost | Stability |")
    lines.append("|----------|--------|----------|---------|------|-----------|")

    for provider_id, metadata in sorted(providers.items()):
        domain = provider_id.split(".")[0].title()
        name = metadata["name"]
        coverage = metadata["technical"]["coverage"]
        auth = metadata["technical"]["authentication"]
        api_key = "Required" if auth != "none" else "No"
        cost = metadata["cost"]["pricing_model"]
        stability = metadata["reliability"]["stability"].upper()

        lines.append(
            f"| {name} | {domain} | {coverage} | {api_key} | {cost} | {stability} |"
        )

    lines.append("")
    return "\n".join(lines)


def generate_comparison_by_domain(providers: dict[str, Any]) -> str:
    """Generate comparison tables grouped by domain."""
    lines = []
    lines.append("## Comparison by Domain")
    lines.append("")

    # Group by domain
    by_domain: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for provider_id, metadata in providers.items():
        domain = provider_id.split(".")[0]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append((provider_id, metadata))

    # Generate table for each domain
    for domain in sorted(by_domain.keys()):
        lines.append(f"### {domain.title()}")
        lines.append("")

        # Different columns for different domains
        if domain in ("elevation", "weather"):
            lines.append(
                "| Provider | Resolution | Coverage | Data Quality | Best For |"
            )
            lines.append(
                "|----------|------------|----------|--------------|----------|"
            )

            for _provider_id, metadata in sorted(by_domain[domain]):
                name = metadata["name"]
                resolution = metadata["technical"]["resolution"]
                coverage = metadata["technical"]["coverage"]
                quality = metadata["reliability"]["data_quality"]
                best_for = (
                    metadata["use_cases"]["best_for"][0]
                    if metadata["use_cases"]["best_for"]
                    else "General"
                )

                lines.append(
                    f"| {name} | {resolution} | {coverage} | {quality} | {best_for} |"
                )

        elif domain == "soil":
            lines.append("| Provider | Coverage | Resolution | Depths | Best For |")
            lines.append("|----------|----------|------------|--------|----------|")

            for _provider_id, metadata in sorted(by_domain[domain]):
                name = metadata["name"]
                coverage = metadata["technical"]["coverage"]
                resolution = metadata["technical"]["resolution"]
                # Extract depths info from strengths or description
                depths = "Multiple"
                best_for = (
                    metadata["use_cases"]["best_for"][0]
                    if metadata["use_cases"]["best_for"]
                    else "General"
                )

                lines.append(
                    f"| {name} | {coverage} | {resolution} | {depths} | {best_for} |"
                )

        elif domain in ("marine", "land"):
            lines.append("| Provider | Coverage | Resolution | Data Type | Best For |")
            lines.append("|----------|----------|------------|-----------|----------|")

            for _provider_id, metadata in sorted(by_domain[domain]):
                name = metadata["name"]
                coverage = metadata["technical"]["coverage"]
                resolution = metadata["technical"]["resolution"]
                data_type = metadata["technical"]["data_source"]
                best_for = (
                    metadata["use_cases"]["best_for"][0]
                    if metadata["use_cases"]["best_for"]
                    else "General"
                )

                lines.append(
                    f"| {name} | {coverage} | {resolution} | {data_type} | {best_for} |"
                )

        else:  # geocoding, etc.
            lines.append("| Provider | Coverage | API Key | Cost | Best For |")
            lines.append("|----------|----------|---------|------|----------|")

            for _provider_id, metadata in sorted(by_domain[domain]):
                name = metadata["name"]
                coverage = metadata["technical"]["coverage"]
                api_key = (
                    "Required"
                    if metadata["technical"]["authentication"] != "none"
                    else "No"
                )
                cost = metadata["cost"]["pricing_model"]
                best_for = (
                    metadata["use_cases"]["best_for"][0]
                    if metadata["use_cases"]["best_for"]
                    else "General"
                )

                lines.append(
                    f"| {name} | {coverage} | {api_key} | {cost} | {best_for} |"
                )

        lines.append("")

    return "\n".join(lines)


def generate_provider_profile(metadata: dict[str, Any]) -> str:
    """Generate detailed profile for a single provider."""
    lines = []

    # Header
    lines.append(f"## {metadata['name']}")
    lines.append("")
    lines.append(f"**{metadata['technical']['data_source']}**")
    lines.append("")

    # Quick facts
    lines.append("### Quick Facts")
    lines.append("")
    tech = metadata["technical"]
    lines.append(f"- **API Type**: {tech['api_type']}")
    if tech.get("api_endpoint"):
        lines.append(f"- **Endpoint**: {tech['api_endpoint']}")
    lines.append(f"- **Authentication**: {tech['authentication']}")
    if tech.get("api_key_env_var"):
        lines.append(f"- **API Key**: `{tech['api_key_env_var']}`")
    lines.append(f"- **Coverage**: {tech['coverage']}")
    lines.append(f"- **Resolution**: {tech['resolution']}")
    if tech.get("temporal_coverage"):
        lines.append(f"- **Temporal**: {tech['temporal_coverage']}")
    if tech.get("data_freshness"):
        lines.append(f"- **Freshness**: {tech['data_freshness']}")
    lines.append("")

    # Reliability
    rel = metadata["reliability"]
    lines.append("### Reliability")
    lines.append("")
    lines.append(f"- **Stability**: {rel['stability'].upper()}")
    lines.append(f"- **Data Quality**: {rel['data_quality']}")
    lines.append(f"- **Uptime**: {rel['uptime_history']}")
    if rel.get("known_issues"):
        lines.append("- **Known Issues**:")
        for issue in rel["known_issues"]:
            lines.append(f"  - {issue}")
    lines.append("")

    # Cost
    cost = metadata["cost"]
    lines.append("### Cost")
    lines.append("")
    lines.append(f"- **Pricing Model**: {cost['pricing_model']}")
    lines.append(f"- **Free Tier**: {cost['free_tier']}")
    if cost.get("quota_limits") and cost["quota_limits"] != "None":
        lines.append(f"- **Quotas**: {cost['quota_limits']}")
    lines.append("")

    # Strengths & Weaknesses side-by-side
    lines.append("### Strengths & Weaknesses")
    lines.append("")
    lines.append("| Strengths | Weaknesses |")
    lines.append("|-----------|------------|")

    # Pad lists to same length
    strengths = metadata["strengths"]
    weaknesses = metadata["weaknesses"]
    max_len = max(len(strengths), len(weaknesses))

    for i in range(max_len):
        strength = f"✓ {strengths[i]}" if i < len(strengths) else ""
        weakness = f"✗ {weaknesses[i]}" if i < len(weaknesses) else ""
        lines.append(f"| {strength} | {weakness} |")

    lines.append("")

    # Use cases
    use_cases = metadata["use_cases"]
    lines.append("### Use Cases")
    lines.append("")
    lines.append("**Best For:**")
    for case in use_cases["best_for"]:
        lines.append(f"- {case}")
    lines.append("")

    lines.append("**Not Suitable For:**")
    for case in use_cases["not_suitable_for"]:
        lines.append(f"- {case}")
    lines.append("")

    if use_cases.get("complements"):
        lines.append("**Complements:**")
        for comp in use_cases["complements"]:
            lines.append(f"- {comp}")
        lines.append("")

    # NMDC integration
    nmdc = metadata["nmdc_integration"]
    lines.append("### NMDC Integration")
    lines.append("")
    lines.append(f"- **Schema Slots**: {', '.join(nmdc['schema_slots'])}")
    lines.append(f"- **Role**: {nmdc['multi_provider_role']}")
    if nmdc["geographic_preferences"].get("excellent"):
        lines.append(
            f"- **Excellent For**: {', '.join(nmdc['geographic_preferences']['excellent'])}"
        )
    if nmdc["geographic_preferences"].get("poor"):
        lines.append(
            f"- **Poor For**: {', '.join(nmdc['geographic_preferences']['poor'])}"
        )
    lines.append("")

    # Reference
    if tech.get("api_endpoint"):
        lines.append(f"**API Documentation**: {tech['api_endpoint']}")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate_markdown_documentation(providers: dict[str, Any]) -> str:
    """Generate complete markdown documentation."""
    lines = []

    # Header
    lines.append("# Provider Documentation")
    lines.append("")
    lines.append(
        "This document provides comprehensive information about all data providers "
        "available in the biosample-enricher package."
    )
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    lines.append("1. [Provider Overview](#provider-overview)")
    lines.append("2. [Comparison by Domain](#comparison-by-domain)")

    # Group providers by domain for TOC
    by_domain: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for provider_id, metadata in providers.items():
        domain = provider_id.split(".")[0]
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append((provider_id, metadata))

    # Add domain sections to TOC
    for domain in sorted(by_domain.keys()):
        lines.append(f"   - [{domain.title()}](#comparison-by-domain)")

    lines.append("3. [Detailed Provider Profiles](#detailed-provider-profiles)")

    # Add individual providers to TOC
    for _provider_id, metadata in sorted(providers.items()):
        name = metadata["name"]
        anchor = name.lower().replace(" ", "-").replace("(", "").replace(")", "")
        lines.append(f"   - [{name}](#{anchor})")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Overview table
    lines.append(generate_overview_table(providers))
    lines.append("")

    # Comparison by domain
    lines.append(generate_comparison_by_domain(providers))
    lines.append("")

    # Detailed profiles
    lines.append("# Detailed Provider Profiles")
    lines.append("")
    lines.append(
        "Below are comprehensive profiles for each provider, including technical "
        "specifications, reliability information, and use case recommendations."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    for _provider_id, metadata in sorted(providers.items()):
        lines.append(generate_provider_profile(metadata))

    # Footer
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*This documentation was automatically generated from `config/provider_metadata.yaml` "
        "by `scripts/generate_provider_docs.py`*"
    )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate markdown documentation from provider metadata"
    )
    parser.add_argument(
        "--output",
        default="docs/PROVIDERS.md",
        help="Output file path (default: docs/PROVIDERS.md)",
    )
    args = parser.parse_args()

    # Load metadata
    config_path = Path("config/provider_metadata.yaml")
    if not config_path.exists():
        print(f"❌ Metadata file not found: {config_path}")
        return 1

    print(f"Loading metadata: {config_path}")

    providers = load_provider_metadata(config_path)
    print(f"Found {len(providers)} providers")

    # Generate markdown
    markdown = generate_markdown_documentation(providers)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(markdown)

    print(f"✓ Generated documentation: {output_path}")

    # Summary by domain
    by_domain: dict[str, int] = {}
    for provider_id in providers:
        domain = provider_id.split(".")[0]
        by_domain[domain] = by_domain.get(domain, 0) + 1

    print("\nProviders by domain:")
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain}: {count}")

    return 0


if __name__ == "__main__":
    exit(main())
