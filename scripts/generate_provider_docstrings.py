#!/usr/bin/env python3
"""
Generate provider class docstrings from metadata YAML.

This script reads config/provider_metadata.yaml and generates structured
docstrings for all provider classes, integrating strengths, weaknesses,
and systematic comparison criteria directly into Python code.

Usage:
    python scripts/generate_provider_docstrings.py [--dry-run] [--provider elevation.google]
"""

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


def load_provider_metadata(config_path: Path) -> dict[str, Any]:
    """Load provider metadata from YAML file."""
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data["providers"]


def generate_docstring(metadata: dict[str, Any]) -> str:
    """
    Generate a comprehensive docstring from provider metadata.

    Args:
        metadata: Provider metadata dictionary

    Returns:
        Formatted docstring text
    """
    lines = []

    # Header
    lines.append('    """')
    lines.append(f"    {metadata['name']} - {metadata['technical']['data_source']}")
    lines.append("")

    # Technical overview
    lines.append("    Technical Characteristics:")
    tech = metadata["technical"]
    lines.append(f"        API Type: {tech['api_type']}")
    if tech.get("api_endpoint"):
        lines.append(f"        Endpoint: {tech['api_endpoint']}")
    lines.append(f"        Authentication: {tech['authentication']}")
    if tech.get("api_key_env_var"):
        lines.append(f"        API Key: {tech['api_key_env_var']}")
    lines.append(f"        Coverage: {tech['coverage']}")
    lines.append(f"        Resolution: {tech['resolution']}")
    if tech.get("temporal_coverage"):
        lines.append(f"        Temporal: {tech['temporal_coverage']}")
    if tech.get("data_freshness"):
        lines.append(f"        Freshness: {tech['data_freshness']}")
    lines.append("")

    # Reliability
    rel = metadata["reliability"]
    lines.append("    Reliability:")
    lines.append(f"        Stability: {rel['stability'].upper()}")
    lines.append(f"        Data Quality: {rel['data_quality']}")
    lines.append(f"        Uptime: {rel['uptime_history']}")
    if rel.get("known_issues"):
        lines.append("        Known Issues:")
        for issue in rel["known_issues"]:
            lines.append(f"            - {issue}")
    lines.append("")

    # Cost
    cost = metadata["cost"]
    lines.append("    Cost:")
    lines.append(f"        Model: {cost['pricing_model']}")
    lines.append(f"        Free Tier: {cost['free_tier']}")
    if cost.get("quota_limits") and cost["quota_limits"] != "None":
        lines.append(f"        Quotas: {cost['quota_limits']}")
    lines.append("")

    # Strengths
    lines.append("    Strengths:")
    for strength in metadata["strengths"]:
        lines.append(f"        ✓ {strength}")
    lines.append("")

    # Weaknesses
    lines.append("    Weaknesses:")
    for weakness in metadata["weaknesses"]:
        lines.append(f"        ✗ {weakness}")
    lines.append("")

    # Use cases
    use_cases = metadata["use_cases"]
    lines.append("    Best For:")
    for case in use_cases["best_for"]:
        lines.append(f"        • {case}")
    lines.append("")

    lines.append("    Not Suitable For:")
    for case in use_cases["not_suitable_for"]:
        lines.append(f"        • {case}")
    lines.append("")

    if use_cases.get("complements"):
        lines.append("    Complements:")
        for comp in use_cases["complements"]:
            lines.append(f"        • {comp}")
        lines.append("")

    # NMDC integration
    nmdc = metadata["nmdc_integration"]
    lines.append("    NMDC Integration:")
    lines.append(f"        Schema Slots: {', '.join(nmdc['schema_slots'])}")
    lines.append(f"        Role: {nmdc['multi_provider_role']}")
    if nmdc["geographic_preferences"].get("excellent"):
        lines.append(
            f"        Excellent For: {', '.join(nmdc['geographic_preferences']['excellent'])}"
        )
    if nmdc["geographic_preferences"].get("poor"):
        lines.append(
            f"        Poor For: {', '.join(nmdc['geographic_preferences']['poor'])}"
        )
    lines.append("")

    # Reference
    lines.append("    See Also:")
    lines.append("        Full comparison: config/provider_metadata.yaml")
    if tech.get("api_endpoint"):
        lines.append(f"        API: {tech['api_endpoint']}")

    lines.append('    """')

    return "\n".join(lines)


def find_class_in_file(file_path: Path, class_name: str) -> tuple[int, int] | None:
    """
    Find the line range for a class definition in a Python file.

    Returns:
        (start_line, end_line) of the class docstring, or None if not found
    """
    with open(file_path) as f:
        lines = f.readlines()

    # Find class definition
    class_pattern = re.compile(rf"^class {class_name}\(")
    class_line = None

    for i, line in enumerate(lines):
        if class_pattern.match(line):
            class_line = i
            break

    if class_line is None:
        return None

    # Find existing docstring bounds
    # Look for opening """ or '''
    docstring_start = None
    for i in range(class_line + 1, min(class_line + 10, len(lines))):
        if '"""' in lines[i] or "'''" in lines[i]:
            docstring_start = i
            break

    if docstring_start is None:
        # No docstring exists, return position after class definition
        return (class_line + 1, class_line + 1)

    # Find closing """ or '''
    quote_type = '"""' if '"""' in lines[docstring_start] else "'''"
    docstring_end = None

    # Check if it's a one-line docstring
    if lines[docstring_start].count(quote_type) >= 2:
        return (docstring_start, docstring_start + 1)

    # Multi-line docstring
    for i in range(docstring_start + 1, min(docstring_start + 200, len(lines))):
        if quote_type in lines[i]:
            docstring_end = i + 1
            break

    if docstring_end is None:
        return None

    return (docstring_start, docstring_end)


def update_provider_file(
    _provider_id: str, metadata: dict[str, Any], dry_run: bool = False
) -> bool:
    """
    Update a provider file with generated docstring.

    Args:
        _provider_id: Provider identifier (unused, kept for API compatibility)
        metadata: Provider metadata dictionary
        dry_run: If True, only print what would be changed

    Returns:
        True if updated successfully
    """
    module_path = metadata["module"].replace("biosample_enricher.", "")
    file_path = Path("biosample_enricher") / module_path.replace(".", "/")
    file_path = file_path.with_suffix(".py")

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    class_name = metadata["class"]

    # Find class docstring location
    docstring_range = find_class_in_file(file_path, class_name)
    if docstring_range is None:
        print(f"❌ Could not find class {class_name} in {file_path}")
        return False

    # Generate new docstring
    new_docstring = generate_docstring(metadata)

    # Read original file
    with open(file_path) as f:
        lines = f.readlines()

    # Replace docstring
    start_line, end_line = docstring_range
    new_lines = lines[:start_line] + [new_docstring + "\n"] + lines[end_line:]

    if dry_run:
        print(f"\n{'=' * 80}")
        print(f"Would update: {file_path}")
        print(f"  Class: {class_name}")
        print(f"  Lines: {start_line}-{end_line}")
        print(f"\n{'-' * 80}")
        print("New docstring:")
        print(f"{'-' * 80}")
        print(new_docstring)
        print(f"{'=' * 80}\n")
        return True

    # Write updated file
    with open(file_path, "w") as f:
        f.writelines(new_lines)

    print(f"✓ Updated {file_path} - {class_name}")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate provider docstrings from metadata YAML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument(
        "--provider",
        help="Only update specific provider (e.g., elevation.google)",
    )
    args = parser.parse_args()

    # Load metadata
    config_path = Path("config/provider_metadata.yaml")
    if not config_path.exists():
        print(f"❌ Metadata file not found: {config_path}")
        return 1

    providers = load_provider_metadata(config_path)

    # Filter to specific provider if requested
    if args.provider:
        if args.provider not in providers:
            print(f"❌ Provider not found: {args.provider}")
            print(f"Available: {', '.join(sorted(providers.keys()))}")
            return 1
        providers = {args.provider: providers[args.provider]}

    # Update all providers
    success_count = 0
    fail_count = 0

    for provider_id, metadata in sorted(providers.items()):
        try:
            if update_provider_file(provider_id, metadata, dry_run=args.dry_run):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ Error updating {provider_id}: {e}")
            fail_count += 1

    # Summary
    print(f"\n{'=' * 80}")
    print(f"Summary: {success_count} updated, {fail_count} failed")
    if args.dry_run:
        print("(Dry run - no files were modified)")
    print(f"{'=' * 80}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit(main())
