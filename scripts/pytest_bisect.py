#!/usr/bin/env python3
"""
Pytest bisector to find the first test that poisons another test.

Finds the earliest test that, when run before a victim test, causes it to fail.
"""

import subprocess
import sys
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def coll():
    """Collect all test node IDs."""
    r = subprocess.run(
        ["uv", "run", "pytest", "tests/", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True
    )
    items = [
        ln.split()[0] for ln in r.stdout.splitlines()
        if "::" in ln and not ln.startswith("<") and not ln.startswith("=")
    ]
    return items


def ok(pre, victim):
    """Test if victim passes when run after pre tests."""
    cmd = ["uv", "run", "pytest", "-q"] + pre + ["-q", victim]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0


def bisect(victim, items):
    """Binary search to find first poisoning test."""
    lo, hi = 0, len(items)
    guilty = None
    while lo < hi:
        mid = (lo + hi) // 2
        pre = items[:mid]
        print(f"Testing with {len(pre)} tests before {victim}...")
        if ok(pre, victim):
            lo = mid + 1
        else:
            guilty = mid
            hi = mid
    return items[guilty] if guilty is not None else None


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/pytest_bisect.py <victim-test-nodeid>")
        print()
        print("Example:")
        print("  uv run python scripts/pytest_bisect.py tests/test_google_apis.py::TestGoogleAPIsIntegration::test_google_elevation_api")
        sys.exit(2)
        
    victim = sys.argv[1]
    print(f"🔍 Finding poisoner for: {victim}")
    
    items = coll()
    print(f"📋 Collected {len(items)} total tests")
    
    # First check if victim passes alone
    print("🧪 Testing victim in isolation...")
    if not ok([], victim):
        print(f"❌ {victim} fails even in isolation - not an order dependency")
        return 1
    
    print("✅ Victim passes alone - looking for poisoner...")
    
    g = bisect(victim, items)
    if g:
        print(f"🎯 First poisoning test before {victim} is:")
        print(f"   {g}")
        print()
        print("🧪 To verify:")
        print(f"   uv run pytest -q {g} {victim}")
    else:
        print("🤔 No order-coupled poisoner found.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())