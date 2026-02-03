name: "Performance Testing Samples"
description: "Examples of performance testing patterns"

## Pattern 1: Simple Benchmark

This benchmark tests with 10 concurrent workers:

```bash
aclip --env_path .env benchmark \
  --payload_path payload_simple.json \
  --num_workers 10 \
  --verbose
```

## Pattern 2: Load Testing

Progressive load testing to find agent limits:

```bash
#!/bin/bash
for workers in 5 10 25 50 100; do
  echo "Testing with $workers workers..."
  aclip --env_path .env benchmark \
    --payload_path payload_simple.json \
    --num_workers $workers \
    --verbose
done
```

## Pattern 3: Async Benchmarking

Use async workers for higher concurrency:

```bash
aclip --env_path .env benchmark \
  --payload_path payload_simple.json \
  --num_workers 100 \
  --async_mode \
  --verbose
```

## Pattern 4: Different Payloads

Compare performance with different message types:

```bash
# Simple
aclip --env_path .env benchmark -p payload_simple.json -n 50

# Complex
aclip --env_path .env benchmark -p payload_complex.json -n 50
```

## Files

- `payload_simple.json` - Simple test message
- `payload_complex.json` - Complex message with multiple fields

## Expected Results

Good performance results should show:
- Mean response time < 500ms
- Success rate 100%
- Consistent throughput across workers

## See Also

[PERFORMANCE_TESTING.md](../../guides/PERFORMANCE_TESTING.md)
