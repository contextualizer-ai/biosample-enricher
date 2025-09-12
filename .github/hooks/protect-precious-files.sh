#!/bin/bash
# Pre-commit hook to protect precious LLM-generated files from accidental deletion

# List of precious files that should not be accidentally deleted
PRECIOUS_FILES=(
    "data/outputs/schema/enrichment_analysis.json"
    "data/outputs/schema/enrichment_analysis_raw.json" 
    "data/outputs/schema/schema_comparison.json"
    "data/outputs/schema/schema_comparison_raw.json"
)

# Check if any precious files are being deleted
deleted_precious_files=()

for file in "${PRECIOUS_FILES[@]}"; do
    # Check if file is being deleted (exists in index but being removed)
    if git diff --cached --name-only --diff-filter=D | grep -q "^$file$"; then
        deleted_precious_files+=("$file")
    fi
done

# If precious files are being deleted, warn and potentially block
if [ ${#deleted_precious_files[@]} -gt 0 ]; then
    echo ""
    echo "🛡️  ⚠️  WARNING: Precious LLM-generated files are being deleted!"
    echo ""
    for file in "${deleted_precious_files[@]}"; do
        echo "   📄 $file"
    done
    echo ""
    echo "These files contain valuable LLM-generated schema analysis that is"
    echo "expensive to reproduce. Consider one of these options:"
    echo ""
    echo "1. Skip this commit and regenerate the files instead:"
    echo "   make analyze-schemas"
    echo ""
    echo "2. Create a backup before proceeding:"
    echo "   mkdir -p .backups/schema/\$(date +%Y%m%d_%H%M%S)"
    echo "   cp data/outputs/schema/enrichment_analysis*.json .backups/schema/\$(date +%Y%m%d_%H%M%S)/"
    echo "   cp data/outputs/schema/schema_comparison*.json .backups/schema/\$(date +%Y%m%d_%H%M%S)/"
    echo ""
    echo "3. Override this protection (if deletion is intentional):"
    echo "   git commit --no-verify"
    echo ""
    
    # For now, just warn but don't block (change to exit 1 to block)
    echo "⚠️  Proceeding with deletion (protection is in warning mode)"
    echo "   Change exit code in scripts/protect-precious-files.sh to block deletions"
    echo ""
    
    # Uncomment the next line to actually block the commit:
    # exit 1
fi

# Always succeed for now (change to blocking behavior above if desired)
exit 0