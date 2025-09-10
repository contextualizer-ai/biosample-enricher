#!/usr/bin/env python3
"""
HTTP Cache Management CLI

Command-line utilities for managing HTTP cache using requests-cache.
"""

import json
import time
from typing import Any

import click
from rich.console import Console

from .http_cache import get_session, request

console = Console()


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """HTTP Cache Management CLI."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["session"] = get_session()
    except Exception as e:
        console.print(f"[red]Failed to get cache session: {e}[/red]")
        raise SystemExit(1) from e


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show cache information."""
    session = ctx.obj["session"]

    console.print("[bold]HTTP Cache Information[/bold]")
    console.print(f"Backend: {type(session.cache).__name__}")

    # Try to get cache statistics if available
    if hasattr(session.cache, "db_path"):
        console.print(f"Database path: {session.cache.db_path}")
    elif hasattr(session.cache, "db_name"):
        console.print(f"Database name: {session.cache.db_name}")

    # Show cache size if available
    try:
        keys = list(session.cache.responses.keys())
        console.print(f"Cached responses: {len(keys)}")
    except Exception:
        console.print("Cache statistics not available")


@cli.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clear(ctx: click.Context, confirm: bool) -> None:
    """Clear all cache entries."""
    session = ctx.obj["session"]

    if not confirm and not click.confirm("Clear ALL cache entries. Are you sure?"):
        console.print("Cancelled.")
        return

    try:
        session.cache.clear()
        console.print("[green]Cache cleared successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to clear cache: {e}[/red]")


@cli.command()
@click.argument("url")
@click.option("--method", default="GET", help="HTTP method")
@click.option("--params", help="Query parameters as JSON")
@click.pass_context
def test(
    ctx: click.Context,
    url: str,
    method: str,
    params: str | None,
) -> None:
    """Test cache functionality with a request."""
    session = ctx.obj["session"]

    try:
        # Parse params if provided
        params_dict: dict[str, Any] | None = None
        if params:
            params_dict = json.loads(params)

        console.print(f"Making {method} request to: {url}")
        if params_dict:
            console.print(f"With params: {params_dict}")

        # Clear cache for this test
        session.cache.clear()

        # First request (should miss cache)
        console.print("\n[bold]First request (cache miss expected):[/bold]")
        start_time = time.time()
        response1 = request(method, url, params=params_dict, timeout=10)
        first_time = time.time() - start_time

        from_cache1 = getattr(response1, "from_cache", False)
        console.print(f"Status: {response1.status_code}")
        console.print(f"From cache: {from_cache1}")
        console.print(f"Time: {first_time:.3f}s")
        console.print(f"Response size: {len(response1.content)} bytes")

        # Second request (should hit cache)
        console.print("\n[bold]Second request (cache hit expected):[/bold]")
        start_time = time.time()
        response2 = request(method, url, params=params_dict, timeout=10)
        second_time = time.time() - start_time

        from_cache2 = getattr(response2, "from_cache", False)
        console.print(f"Status: {response2.status_code}")
        console.print(f"From cache: {from_cache2}")
        console.print(f"Time: {second_time:.3f}s")
        console.print(f"Response size: {len(response2.content)} bytes")

        # Verify cache is working
        if from_cache2 and not from_cache1:
            speedup = first_time / second_time if second_time > 0 else float("inf")
            console.print(f"\n[green]✅ Cache working! Speedup: {speedup:.1f}x[/green]")
        else:
            console.print("\n[yellow]⚠️  Cache behavior unexpected[/yellow]")

        # Test coordinate canonicalization if this looks like coords
        if params_dict and any(
            k.lower() in {"lat", "lng", "latitude", "longitude"} for k in params_dict
        ):
            console.print("\n[bold]Testing coordinate canonicalization:[/bold]")
            # Add some precision to coordinates
            canon_params = {}
            for k, v in params_dict.items():
                if k.lower() in {"lat", "lng", "latitude", "longitude"}:
                    try:
                        canon_params[k] = float(v) + 0.000001  # Add tiny precision
                    except (ValueError, TypeError):
                        canon_params[k] = v
                else:
                    canon_params[k] = v

            response3 = request(method, url, params=canon_params, timeout=10)
            from_cache3 = getattr(response3, "from_cache", False)
            console.print(f"High precision coords from cache: {from_cache3}")

            if from_cache3:
                console.print("[green]✅ Coordinate canonicalization working![/green]")

    except Exception as e:
        console.print(f"[red]Test failed: {e}[/red]")


if __name__ == "__main__":
    cli()
