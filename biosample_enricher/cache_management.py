#!/usr/bin/env python3
"""
HTTP Cache Management CLI

Command-line utilities for managing MongoDB-based HTTP cache.
"""

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

import click
from rich.console import Console
from rich.progress import track
from rich.table import Table

from .http_cache import MongoHTTPCache, get_cached_client

console = Console()


@click.group()
@click.option(
    "--mongo-uri",
    default=lambda: os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    help="MongoDB connection URI",
)
@click.option("--database", default="http_cache", help="Database name for cache")
@click.option(
    "--collection", default="requests", help="Collection name for cache entries"
)
@click.pass_context
def cli(ctx: click.Context, mongo_uri: str, database: str, collection: str) -> None:
    """HTTP Cache Management CLI."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["cache"] = MongoHTTPCache(
            mongo_uri=mongo_uri, database=database, collection=collection
        )
    except Exception as e:
        console.print(f"[red]Failed to connect to MongoDB: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--method", help="Filter by HTTP method (GET, POST, etc.)")
@click.option("--url-pattern", help="Filter by URL pattern (substring match)")
@click.option("--status-code", type=int, help="Filter by status code")
@click.option("--hours-back", type=int, help="Show entries from last N hours")
@click.option("--limit", default=50, help="Maximum number of entries to show")
@click.option(
    "--format", "output_format", type=click.Choice(["table", "json"]), default="table"
)
@click.pass_context
def query(
    ctx: click.Context,
    method: str | None,
    url_pattern: str | None,
    status_code: int | None,
    hours_back: int | None,
    limit: int,
    output_format: str,
) -> None:
    """Query and display cache entries."""
    cache = ctx.obj["cache"]

    if not cache._collection:
        console.print("[red]Cache not available[/red]")
        return

    # Build query
    query_filter: dict[str, Any] = {}

    if method:
        query_filter["method"] = method.upper()

    if url_pattern:
        query_filter["url"] = {"$regex": url_pattern, "$options": "i"}

    if status_code:
        query_filter["status_code"] = status_code

    if hours_back:
        since = datetime.now(UTC) - timedelta(hours=hours_back)
        query_filter["created_at"] = {"$gte": since}

    try:
        cursor = (
            cache._collection.find(query_filter).sort("created_at", -1).limit(limit)
        )
        entries = list(cursor)

        if output_format == "json":
            # Convert for JSON output
            for entry in entries:
                if "_id" in entry:
                    entry["_id"] = str(entry["_id"])
                if "created_at" in entry and isinstance(entry["created_at"], datetime):
                    entry["created_at"] = entry["created_at"].isoformat()
                if "expires_at" in entry and isinstance(entry["expires_at"], datetime):
                    entry["expires_at"] = entry["expires_at"].isoformat()
                if "last_accessed" in entry and isinstance(
                    entry["last_accessed"], datetime
                ):
                    entry["last_accessed"] = entry["last_accessed"].isoformat()

            click.echo(json.dumps(entries, indent=2, default=str))
        else:
            # Table format
            if not entries:
                console.print(
                    "[yellow]No cache entries found matching criteria[/yellow]"
                )
                return

            table = Table(
                title=f"Cache Entries (showing {len(entries)} of max {limit})"
            )
            table.add_column("Created", style="dim")
            table.add_column("Method", style="bold")
            table.add_column("Status", style="green")
            table.add_column("URL")
            table.add_column("Hits", justify="right")
            table.add_column("Size", justify="right")

            for entry in entries:
                created = entry.get("created_at", "")
                if isinstance(created, datetime):
                    created = created.strftime("%m-%d %H:%M")

                method = entry.get("method", "")
                status = str(entry.get("status_code", ""))
                url = entry.get("url", "")
                hits = str(entry.get("hit_count", 0))

                # Format response size
                size = len(entry.get("response_body", b""))
                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size // 1024}KB"
                else:
                    size_str = f"{size // (1024 * 1024)}MB"

                # Truncate long URLs
                if len(url) > 60:
                    url = url[:57] + "..."

                # Color code status
                status_color = (
                    "green"
                    if status.startswith("2")
                    else "yellow"
                    if status.startswith("3")
                    else "red"
                )

                table.add_row(
                    created,
                    method,
                    f"[{status_color}]{status}[/{status_color}]",
                    url,
                    hits,
                    size_str,
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show cache statistics."""
    cache = ctx.obj["cache"]

    stats_data = cache.stats()

    if "error" in stats_data:
        console.print(f"[red]Error getting stats: {stats_data['error']}[/red]")
        return

    console.print("[bold]HTTP Cache Statistics[/bold]")
    console.print(f"Total entries: {stats_data.get('total_entries', 0)}")
    console.print(f"Total hits: {stats_data.get('total_hits', 0)}")
    console.print(f"Recent entries (24h): {stats_data.get('recent_entries_24h', 0)}")
    console.print()

    # Status code breakdown
    if stats_data.get("by_status_code"):
        status_table = Table(title="Entries by Status Code")
        status_table.add_column("Status Code")
        status_table.add_column("Count", justify="right")

        for status, count in stats_data["by_status_code"].items():
            status_color = (
                "green"
                if str(status).startswith("2")
                else "yellow"
                if str(status).startswith("3")
                else "red"
            )
            status_table.add_row(
                f"[{status_color}]{status}[/{status_color}]", str(count)
            )

        console.print(status_table)
        console.print()

    # Method breakdown
    if stats_data.get("by_method"):
        method_table = Table(title="Entries by HTTP Method")
        method_table.add_column("Method")
        method_table.add_column("Count", justify="right")

        for method, count in stats_data["by_method"].items():
            method_table.add_row(method, str(count))

        console.print(method_table)


@cli.command()
@click.option(
    "--older-than-hours",
    type=int,
    help="Clear entries older than N hours (if not specified, clears all)",
)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clear(ctx: click.Context, older_than_hours: int | None, confirm: bool) -> None:
    """Clear cache entries."""
    cache = ctx.obj["cache"]

    if older_than_hours:
        message = f"Clear cache entries older than {older_than_hours} hours"
    else:
        message = "Clear ALL cache entries"

    if not confirm and not click.confirm(f"{message}. Are you sure?"):
        console.print("Cancelled.")
        return

    deleted_count = cache.clear(older_than_hours)
    console.print(f"[green]Deleted {deleted_count} cache entries[/green]")


@cli.command()
@click.option("--cache-key", help="Specific cache key to delete")
@click.option("--url-pattern", help="Delete entries matching URL pattern")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete(
    ctx: click.Context, cache_key: str | None, url_pattern: str | None, confirm: bool
) -> None:
    """Delete specific cache entries."""
    cache = ctx.obj["cache"]

    if not cache._collection:
        console.print("[red]Cache not available[/red]")
        return

    if cache_key:
        if not confirm and not click.confirm(f"Delete cache entry {cache_key}?"):
            console.print("Cancelled.")
            return

        success = cache.delete(cache_key)
        if success:
            console.print(f"[green]Deleted cache entry {cache_key}[/green]")
        else:
            console.print(f"[yellow]Cache entry {cache_key} not found[/yellow]")

    elif url_pattern:
        # Find matching entries first
        try:
            query_filter: dict[str, Any] = {
                "url": {"$regex": url_pattern, "$options": "i"}
            }
            matching = list(cache._collection.find(query_filter, {"_id": 1, "url": 1}))

            if not matching:
                console.print("[yellow]No entries found matching URL pattern[/yellow]")
                return

            console.print(f"Found {len(matching)} entries matching pattern:")
            for entry in matching[:5]:  # Show first 5
                console.print(f"  {entry['url']}")
            if len(matching) > 5:
                console.print(f"  ... and {len(matching) - 5} more")

            if not confirm and not click.confirm(
                f"Delete all {len(matching)} matching entries?"
            ):
                console.print("Cancelled.")
                return

            result = cache._collection.delete_many(query_filter)
            console.print(
                f"[green]Deleted {result.deleted_count} cache entries[/green]"
            )

        except Exception as e:
            console.print(f"[red]Delete failed: {e}[/red]")

    else:
        console.print(
            "[yellow]Must specify either --cache-key or --url-pattern[/yellow]"
        )


@cli.command()
@click.option("--output", "-o", required=True, help="Output JSON file")
@click.option("--method", help="Filter by HTTP method")
@click.option("--status-code", type=int, help="Filter by status code")
@click.option("--hours-back", type=int, help="Export entries from last N hours")
@click.option("--limit", default=1000, help="Maximum number of entries to export")
@click.pass_context
def export(
    ctx: click.Context,
    output: str,
    method: str | None,
    status_code: int | None,
    hours_back: int | None,
    limit: int,
) -> None:
    """Export cache entries to JSON file."""
    cache = ctx.obj["cache"]

    if not cache._collection:
        console.print("[red]Cache not available[/red]")
        return

    # Build query
    query_filter: dict[str, Any] = {}
    if method:
        query_filter["method"] = method.upper()
    if status_code:
        query_filter["status_code"] = status_code
    if hours_back:
        since = datetime.now(UTC) - timedelta(hours=hours_back)
        query_filter["created_at"] = {"$gte": since}

    try:
        cursor = (
            cache._collection.find(query_filter).sort("created_at", -1).limit(limit)
        )
        entries = []

        for entry in track(cursor, description="Exporting cache entries..."):
            # Convert ObjectId and datetime to strings
            if "_id" in entry:
                entry["_id"] = str(entry["_id"])
            for date_field in ["created_at", "expires_at", "last_accessed"]:
                if date_field in entry and isinstance(entry[date_field], datetime):
                    entry[date_field] = entry[date_field].isoformat()
            entries.append(entry)

        with open(output, "w") as f:
            json.dump(entries, f, indent=2, default=str)

        console.print(
            f"[green]Exported {len(entries)} cache entries to {output}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")


@cli.command()
@click.argument("url")
@click.option("--method", default="GET", help="HTTP method")
@click.option("--params", help="Query parameters as JSON")
@click.option("--expire-after", type=int, help="Cache expiration in seconds")
@click.pass_context
def test(
    _ctx: click.Context,
    url: str,
    method: str,
    params: str | None,
    expire_after: int | None,
) -> None:
    """Test cache functionality with a request."""
    try:
        # Parse params if provided
        params_dict: dict[str, Any] | None = None
        if params:
            params_dict = json.loads(params)

        # Use the global cached client
        client = get_cached_client()

        console.print(f"Making {method} request to: {url}")
        if params_dict:
            console.print(f"With params: {params_dict}")

        # First request (should miss cache)
        console.print("\n[bold]First request (cache miss expected):[/bold]")
        response1 = client.request(
            method, url, params=params_dict, expire_after=expire_after
        )

        from_cache1 = getattr(response1, "_from_cache", False)
        console.print(f"Status: {response1.status_code}")
        console.print(f"From cache: {from_cache1}")
        console.print(f"Response size: {len(response1.content)} bytes")

        # Second request (should hit cache)
        console.print("\n[bold]Second request (cache hit expected):[/bold]")
        response2 = client.request(
            method, url, params=params_dict, expire_after=expire_after
        )

        from_cache2 = getattr(response2, "_from_cache", False)
        console.print(f"Status: {response2.status_code}")
        console.print(f"From cache: {from_cache2}")
        console.print(f"Response size: {len(response2.content)} bytes")

        # Test cache controls
        console.print("\n[bold]Third request (force refresh):[/bold]")
        response3 = client.request(
            method,
            url,
            params=params_dict,
            read_from_cache=False,
            write_to_cache=True,
            expire_after=expire_after,
        )

        from_cache3 = getattr(response3, "_from_cache", False)
        console.print(f"Status: {response3.status_code}")
        console.print(f"From cache: {from_cache3}")
        console.print(f"Response size: {len(response3.content)} bytes")

        if from_cache2 and not from_cache1 and not from_cache3:
            console.print("\n[green]✅ Cache functionality working correctly![/green]")
        else:
            console.print("\n[yellow]⚠️  Cache behavior unexpected[/yellow]")

    except Exception as e:
        console.print(f"[red]Test failed: {e}[/red]")


if __name__ == "__main__":
    cli()
