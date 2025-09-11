# Performance and API Rate Limiting Notes

## Current Implementation (Simplified Synchronous)

This codebase uses **synchronous, sequential processing** for simplicity and maintainability. While this approach is slower than async/concurrent processing for large datasets, it provides several benefits:

1. **Simpler code** - Easy to read, debug, and maintain
2. **Predictable execution** - Linear flow without concurrency concerns  
3. **Natural rate limiting** - Sequential calls inherently avoid overwhelming APIs

## Rate Limiting Strategy

### Interleaved API Calls (Preferred)
When enriching samples with data from multiple APIs, we use an **interleaved round-robin approach**:

```python
for sample in samples:
    result_a = fetch_from_api_a(sample)  # Call API A
    time.sleep(0.1)  # Courtesy delay
    
    result_b = fetch_from_api_b(sample)  # Call API B  
    time.sleep(0.1)
    
    result_c = fetch_from_api_c(sample)  # Call API C
    time.sleep(0.1)
```

This approach:
- Naturally distributes load across different APIs
- Gives each API time to "rest" between requests
- Avoids hammering a single API with rapid successive calls
- Provides better failure isolation (if one API is down, others still work)

### Why Not Async/Concurrent?

We previously had async code with semaphores for rate limiting, but removed it because:
- Added significant complexity for marginal performance gains
- Made debugging and testing more difficult
- The interleaved approach provides natural rate limiting
- Most use cases don't require high-throughput processing

## Caching Strategy

Caching is our primary method for being respectful to APIs:

1. **Request-level caching** - Cache API responses to avoid duplicate requests
2. **Persistent cache** - Save results to disk for reuse across sessions
3. **Cache TTL** - Respect data freshness requirements while minimizing API calls

See `cache_management.py` for implementation details.

## Performance Expectations

### Sequential Processing Times (Approximate)
- **Small datasets (<50 samples)**: 10-30 seconds
- **Medium datasets (100-500 samples)**: 1-5 minutes  
- **Large datasets (1000+ samples)**: 10-20+ minutes

### Future Optimization Options

If performance becomes critical, consider these options (in order of preference):

1. **Better caching** - Expand cache coverage and improve hit rates
2. **Bulk APIs** - Use batch endpoints where available
3. **Simple threading** - Add basic ThreadPoolExecutor for I/O operations
4. **Async (last resort)** - Reintroduce async only if absolutely necessary

## Design Philosophy

We prioritize:
1. **Simplicity** over raw performance
2. **Respectful API usage** through caching and rate limiting
3. **Maintainability** over premature optimization
4. **Clear, debuggable code** over clever concurrency tricks

Remember: "Premature optimization is the root of all evil" - Donald Knuth