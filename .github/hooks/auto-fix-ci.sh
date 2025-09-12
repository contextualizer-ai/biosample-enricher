#!/bin/bash
# Auto-fix CI issues in a loop until all checks pass

set -e

echo "🔧 Running auto-fix CI loop..."

max_iterations=5
iteration=0

while [ $iteration -lt $max_iterations ]; do
    iteration=$((iteration + 1))
    echo ""
    echo "🔄 Iteration $iteration/$max_iterations"
    
    # Run format and lint fixes
    echo "📝 Auto-formatting code..."
    uv run ruff format biosample_enricher/ tests/ || true
    
    echo "🔍 Auto-fixing lint issues..."
    uv run ruff check --fix biosample_enricher/ tests/ || true
    
    # Check if all issues are resolved
    echo "✅ Running full CI check..."
    if make check-ci; then
        echo ""
        echo "🎉 All CI checks passed!"
        exit 0
    fi
    
    echo "⚠️ Issues remain, continuing to next iteration..."
done

echo ""
echo "❌ Could not auto-fix all issues after $max_iterations iterations"
echo "Manual intervention required"
exit 1