---
name: performance-optimization
description: "Use when something is slow or must meet a budget (latency, slow query, index, memory, startup, bundle, battery, Core Web Vitals): profile, optimize the bottleneck, change one thing, prove the gain."
---
# Performance optimization

**No measurement, no optimization.**

1. **Budget**: state the target and the percentile (p95 latency, cold start, LCP, frame time, memory, bundle KB).
2. **Measure** on a realistic setup: production-like data, release build, low-end device for mobile.
3. **Find the bottleneck** with a profiler or traces, not intuition: Chrome DevTools or Lighthouse, `EXPLAIN`, pprof or py-spy, Instruments, Android Profiler or Perfetto, Macrobenchmark.
4. **Change one thing**. Re-measure. Keep it only if the number moved.
5. **Typical wins by layer**:
   - DB: index to the query, kill N+1, batch, paginate, cache with explicit invalidation.
   - Backend: concurrency, connection pools, streaming, avoid work on the request path.
   - Web: split code, lazy load, size images, remove blocking scripts.
   - Mobile: virtualize lists, size and cache images, move work off the main thread, reduce startup work, shrink binary.
6. **Keep a log of attempts.** A change that does not beat the baseline is reverted, not kept as neutral. Cache only what is expensive, with a defined invalidation.
7. **Guard**: add the budget to CI or a dashboard so it does not regress.

## Red flags
| Thought | Reality |
|---|---|
| "This loop looks slow" | Profile. Intuition is usually wrong. |
| "Memoize everything" | Adds cost and bugs where it does not help. |
| "Faster on my laptop" | Measure on the target hardware. |

## Verify
Before and after numbers on the same setup; budget met; a guard exists; no correctness change (tests green).
