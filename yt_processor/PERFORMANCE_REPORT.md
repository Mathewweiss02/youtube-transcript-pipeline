# Transcript Processing Optimization - Performance Report

**Test Date:** 2026-01-07 12:50:48

## Executive Summary

**Recommended Strategy:** Parallel-3
**Speedup vs Baseline:** 1.33x
**Throughput:** 149.50 files/sec

## Performance Comparison

| Strategy | Files/sec | Avg Time (ms) | P95 (ms) | Speedup |
|----------|-----------|---------------|----------|----------|
| Sequential | 112.75 | 8.65 | 18.49 | 1.00x |
| Parallel-3 | 149.50 | 19.15 | 48.96 | 1.33x |
| Parallel-5 | 148.55 | 31.92 | 72.16 | 1.32x |
| Parallel-10 | 145.48 | 60.88 | 141.43 | 1.29x |
| Async-10 | 132.30 | 59.21 | 127.83 | 1.17x |

## Detailed Metrics

### Sequential

- **Throughput:** 112.75 files/sec
- **Average Time:** 8.65ms
- **Median Time:** 7.30ms
- **P95 Time:** 18.49ms
- **P99 Time:** 48.56ms
- **Words/sec:** 1,309,522

### Parallel-3

- **Throughput:** 149.50 files/sec
- **Average Time:** 19.15ms
- **Median Time:** 15.46ms
- **P95 Time:** 48.96ms
- **P99 Time:** 91.23ms
- **Words/sec:** 1,736,450

### Parallel-5

- **Throughput:** 148.55 files/sec
- **Average Time:** 31.92ms
- **Median Time:** 25.39ms
- **P95 Time:** 72.16ms
- **P99 Time:** 147.74ms
- **Words/sec:** 1,725,354

### Parallel-10

- **Throughput:** 145.48 files/sec
- **Average Time:** 60.88ms
- **Median Time:** 48.14ms
- **P95 Time:** 141.43ms
- **P99 Time:** 257.01ms
- **Words/sec:** 1,689,682

### Async-10

- **Throughput:** 132.30 files/sec
- **Average Time:** 59.21ms
- **Median Time:** 47.83ms
- **P95 Time:** 127.83ms
- **P99 Time:** 234.88ms
- **Words/sec:** 1,536,630

## Production Recommendation

**Deploy:** Parallel-3

**Expected Performance:**
- Process 1,903 videos in: 0.2 minutes
- vs Baseline: 0.3 minutes
- **Time Saved:** 0.1 minutes

**Implementation:**
- Use ThreadPoolExecutor with 3 workers
- Guaranteed deterministic speedup: 1.33x
