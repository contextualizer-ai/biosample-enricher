# Reference Metrics Implementations

This directory contains reference implementations and experimental approaches for metrics evaluation.

## gpt5_contractual_metrics.yaml

**Source**: GPT-5 generated contractual metrics framework (from Issue #134)
**Status**: Reference only - not integrated into production
**Created**: September 2025

### Approach
- **Contractual Metrics**: Each metric defined with eligibility, before, and after functions
- **Mathematical Invariants**: Enforces coverage ≤ 100%, monotonicity (after ≥ before)
- **Stratified Reporting**: By realm (marine/terrestrial/freshwater/host)
- **Sample-level Coverage**: Prevents >100% from multi-provider double-counting
- **Wilson Confidence Intervals**: For small N

### Key Concepts
1. **Eligibility Function**: Which samples qualify for this metric
2. **Before Function**: Data present before enrichment
3. **After Function**: Data present after enrichment
4. **Type**: Additive (coverage increases) vs Aggregator (counts/distances)

### Related Issues
- #133: Demo-Ready Metrics (accuracy requirements)
- #134: Evaluate and Clean Up from-gpt5/ Temporary Artifacts

### Future Integration
If this approach proves valuable for solving >100% coverage bugs, patterns can be extracted and integrated into `biosample_enricher/metrics/evaluator.py` following project architecture standards.
