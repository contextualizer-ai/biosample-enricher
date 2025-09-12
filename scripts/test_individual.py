#!/usr/bin/env python3
"""
Test runner that executes every test individually to demonstrate isolation success.

This script collects all tests and runs them one by one, reporting which ones
pass individually vs fail in the full suite.
"""

import subprocess
import sys
from pathlib import Path


def get_all_tests():
    """Get list of all test items using pytest --collect-only."""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    if result.returncode != 0:
        print(f"Failed to collect tests: {result.stderr}")
        return []
    
    # Parse test items from output
    tests = []
    for line in result.stdout.split('\n'):
        line = line.strip()
        if '::' in line and not line.startswith('<') and not line.startswith('='):
            # Clean up the line to get just the test path
            if ' ' in line:
                test_path = line.split()[0]
            else:
                test_path = line
            if test_path.endswith('.py'):
                continue  # Skip file names, we want function names
            tests.append(test_path)
    
    return tests


def run_individual_test(test_path):
    """Run a single test and return (success, output)."""
    result = subprocess.run(
        ["uv", "run", "pytest", test_path, "-v"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    return result.returncode == 0, result.stdout, result.stderr


def main():
    """Run all tests individually and report results."""
    print("🔍 Collecting all tests...")
    tests = get_all_tests()
    
    if not tests:
        print("❌ No tests found!")
        return 1
    
    print(f"📋 Found {len(tests)} tests")
    print("🚀 Running each test individually...\n")
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for i, test in enumerate(tests, 1):
        print(f"[{i:3d}/{len(tests)}] {test:<60}", end=" ")
        
        success, stdout, stderr = run_individual_test(test)
        
        if success:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1
            failed_tests.append((test, stderr))
    
    print(f"\n📊 Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test, error in failed_tests:
            print(f"   • {test}")
            # Show first line of error for brevity
            if error:
                first_error_line = error.split('\n')[0].strip()
                if first_error_line:
                    print(f"     └─ {first_error_line}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())