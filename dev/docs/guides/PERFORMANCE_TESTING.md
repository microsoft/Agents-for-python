# Performance Testing Guide

Learn how to benchmark and optimize your Microsoft Agent's performance.

## Introduction

Performance testing ensures your agent:
- Responds within acceptable time limits
- Handles concurrent requests
- Doesn't degrade under load
- Uses resources efficiently

## Types of Performance Tests

### 1. Response Time Testing

Measure how fast your agent responds to individual requests.

```python
import time
import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_response_time(self, agent_client, response_client):
    """Test single request response time"""
    
    start_time = time.time()
    await agent_client.send_activity("Hello")
    responses = await response_client.pop()
    duration = time.time() - start_time
    
    # Assert time < 1 second
    assert duration < 1.0, f"Response took {duration:.2f}s"
    print(f"Response time: {duration*1000:.0f}ms")
```

### 2. Load Testing

Test how your agent handles multiple concurrent requests.

```python
import asyncio
import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_requests(self, agent_client, response_client):
    """Test multiple concurrent requests"""
    
    # Send 10 messages concurrently
    tasks = [
        agent_client.send_activity(f"Message {i}")
        for i in range(10)
    ]
    
    # Wait for all to complete
    await asyncio.gather(*tasks)
    
    # Collect responses
    responses = await response_client.pop()
    
    # Verify all processed
    assert len(responses) >= 10
```

### 3. Throughput Testing

Measure requests per second your agent can handle.

```python
import time
import pytest

@pytest.mark.performance
@pytest.mark.asyncio
async def test_throughput(self, agent_client, response_client):
    """Test throughput (requests/second)"""
    
    num_requests = 50
    start_time = time.time()
    
    # Send messages
    for i in range(num_requests):
        await agent_client.send_activity(f"Message {i}")
    
    duration = time.time() - start_time
    throughput = num_requests / duration
    
    print(f"Throughput: {throughput:.1f} requests/second")
    assert throughput > 1.0, f"Throughput too low: {throughput:.1f} req/s"
```

## Using the Benchmark CLI

The CLI provides powerful benchmarking capabilities.

### Basic Benchmark

```bash
# Single worker baseline
aclip --env_path .env benchmark \
  --payload_path ./payload.json \
  --num_workers 1
```

### Progressive Load Testing

```bash
# Test with increasing load
for workers in 1 5 10 25 50; do
  echo "Testing with $workers workers..."
  aclip --env_path .env benchmark \
    --payload_path ./payload.json \
    --num_workers $workers
done
```

### Async Benchmarking

```bash
# Use async workers (better for high concurrency)
aclip --env_path .env benchmark \
  --payload_path ./payload.json \
  --num_workers 100 \
  --async_mode \
  --verbose
```

## Payload Creation for Benchmarking

### Simple Payload

```json
{
  "type": "message",
  "text": "Simple test",
  "from": {"id": "user1", "name": "Tester"},
  "conversation": {"id": "conv1"},
  "channelId": "directline"
}
```

### Complex Payload

```json
{
  "type": "message",
  "text": "Complex message with multiple fields",
  "from": {
    "id": "user123",
    "name": "Test User",
    "aadObjectId": "test-aad-id"
  },
  "conversation": {
    "id": "conv123",
    "name": "Test Conversation"
  },
  "channelId": "directline",
  "locale": "en-US",
  "localTimestamp": "2024-01-07T10:00:00Z",
  "timestamp": "2024-01-07T10:00:00Z"
}
```

## Understanding Benchmark Results

### Sample Output

```
Starting benchmark with 10 workers...
Total requests: 100

=== Timing (seconds) ===
Min:     0.123
Max:     0.892
Mean:    0.456
Median:  0.445

=== Status ===
Successful: 100
Failed:     0
Success Rate: 100.0%

=== Throughput ===
Requests/second: 21.9
```

### Interpreting Results

| Metric | What It Means | Good Value |
|--------|---------------|-----------|
| **Min** | Fastest response | N/A (context dependent) |
| **Max** | Slowest response | Should be < 2 seconds |
| **Mean** | Average response | < 500ms for most agents |
| **Median** | Middle response (robust average) | Close to mean |
| **Success Rate** | % successful requests | 100% |
| **Throughput** | Requests per second | Agent dependent |

## Performance Testing Scenarios

### Scenario 1: Simple Message Processing

```bash
# Create simple payload
cat > simple.json << 'EOF'
{
  "type": "message",
  "text": "Hi",
  "from": {"id": "user", "name": "Tester"},
  "conversation": {"id": "conv"},
  "channelId": "directline"
}
EOF

# Benchmark simple processing
aclip --env_path .env benchmark -p ./simple.json -n 50 -v
```

### Scenario 2: Complex Query Processing

```bash
# Create complex query
cat > complex.json << 'EOF'
{
  "type": "message",
  "text": "What is the capital of France and what's its population and give me some history?",
  "from": {"id": "user", "name": "Tester"},
  "conversation": {"id": "conv"},
  "channelId": "directline"
}
EOF

# Benchmark with longer timeout
aclip --env_path .env benchmark -p ./complex.json -n 20 -v
```

### Scenario 3: Rapid Fire Messages

```bash
# Test rapid sequential messages
@pytest.mark.performance
@pytest.mark.asyncio
async def test_rapid_fire_messages(self, agent_client, response_client):
    """Test handling of rapid sequential messages"""
    
    import time
    
    messages = ["Hi"] * 20  # 20 rapid messages
    start = time.time()
    
    for msg in messages:
        await agent_client.send_activity(msg)
    
    duration = time.time() - start
    msg_per_sec = len(messages) / duration
    
    print(f"Rapid fire: {msg_per_sec:.1f} messages/sec")
    assert msg_per_sec > 5.0
```

## Performance Testing Best Practices

### 1. Establish Baselines

Before optimization, understand current performance:

```bash
# Baseline test
aclip --env_path .env benchmark \
  --payload_path ./baseline.json \
  --num_workers 10 \
  > baseline_results.txt

# Later, compare
aclip --env_path .env benchmark \
  --payload_path ./baseline.json \
  --num_workers 10 \
  > optimized_results.txt

# Compare results
diff baseline_results.txt optimized_results.txt
```

### 2. Test Different Payload Sizes

```bash
# Small payload
aclip --env_path .env benchmark -p ./small.json -n 50

# Medium payload
aclip --env_path .env benchmark -p ./medium.json -n 50

# Large payload
aclip --env_path .env benchmark -p ./large.json -n 50
```

### 3. Incremental Load Testing

```bash
#!/bin/bash
# incremental_load_test.sh

echo "Incremental Load Testing"
echo "======================="

for workers in 1 5 10 25 50 100; do
  echo ""
  echo "Testing with $workers workers..."
  
  aclip --env_path .env benchmark \
    --payload_path ./payload.json \
    --num_workers $workers \
    --verbose 2>&1 | grep -E "Throughput|Success|Max|Mean"
done
```

### 4. Monitor Resource Usage

Monitor while running benchmarks:

```bash
# Terminal 1: Run benchmark
aclip --env_path .env benchmark \
  --payload_path ./payload.json \
  --num_workers 50 \
  --async_mode

# Terminal 2: Monitor (on Windows)
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /S .
# Or use Task Manager

# Terminal 2: Monitor (on macOS/Linux)
top -p $(pgrep -f 'python.*agents')
```

## Performance Profiling

### Using cProfile

```python
import cProfile
import pstats
from io import StringIO

@pytest.mark.performance
@pytest.mark.asyncio
async def test_with_profiling(self, agent_client, response_client):
    """Profile agent performance"""
    
    pr = cProfile.Profile()
    pr.enable()
    
    # Run operation
    for _ in range(10):
        await agent_client.send_activity("Test")
    responses = await response_client.pop()
    
    pr.disable()
    
    # Print stats
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)  # Top 10 functions
    print(s.getvalue())
```

### Memory Profiling

```python
import tracemalloc

@pytest.mark.performance
@pytest.mark.asyncio
async def test_memory_usage(self, agent_client, response_client):
    """Profile memory usage"""
    
    tracemalloc.start()
    
    # Send many messages
    for i in range(100):
        await agent_client.send_activity(f"Message {i}")
    
    responses = await response_client.pop()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current: {current / 1024:.1f} KB")
    print(f"Peak: {peak / 1024:.1f} KB")
    
    tracemalloc.stop()
```

## Performance Optimization Tips

### Common Bottlenecks

1. **Slow External Calls**
   - Cache responses
   - Use timeouts
   - Implement retry logic

2. **Memory Leaks**
   - Close connections properly
   - Clear caches periodically
   - Monitor memory usage

3. **Inefficient Algorithms**
   - Profile code
   - Optimize hot paths
   - Use async/await properly

### Optimization Checklist

```python
# ✓ Use async operations
async def handle_request():
    result = await slow_operation()
    return result

# ✓ Reuse connections
client = AgentClient(...)
# Reuse instead of creating new

# ✓ Implement caching
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(param):
    return result

# ✓ Use connection pooling
# Implemented by framework automatically

# ✓ Optimize I/O
# Use async I/O, not blocking calls

# ✓ Profile regularly
# Run benchmarks before/after changes
```

## Reporting Performance Results

### Performance Report Template

```markdown
# Performance Test Report
Date: 2024-01-07

## Configuration
- Agent: MyAgent v1.0
- Python: 3.11
- Environment: Test

## Baseline Results
- Single Request: 456ms
- Throughput: 21.9 req/sec
- Success Rate: 100%

## Load Test Results (50 workers)
- Min: 123ms
- Max: 892ms
- Mean: 456ms
- Median: 445ms
- Throughput: 21.9 req/sec

## Memory Usage
- Current: 45.2 MB
- Peak: 123.4 MB

## Conclusions
- Performance is acceptable for expected load
- No memory leaks detected
- Throughput meets requirements

## Recommendations
- Monitor response times in production
- Set alerts for degradation > 20%
```

## CI/CD Integration

### GitHub Actions Performance Test

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on: [push]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: pip install microsoft-agents-testing
      
      - name: Run Baseline Benchmark
        run: |
          aclip --env_path .env benchmark \
            --payload_path ./payload.json \
            --num_workers 10 \
            > baseline.txt
      
      - name: Store Results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: baseline.txt
```

## Complete Performance Test Suite

```python
import pytest
import time
from microsoft_agents.testing import Integration, AgentClient, ResponseClient

class TestAgentPerformance(Integration):
    """Comprehensive performance tests"""
    
    _agent_url = "http://localhost:3978/"
    _service_url = "http://localhost:8001/"
    _config_path = ".env"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_response_time(self, agent_client, response_client):
        """Test single message response time"""
        start = time.time()
        await agent_client.send_activity("Test")
        responses = await response_client.pop()
        duration = time.time() - start
        
        assert duration < 1.0
        print(f"Response time: {duration*1000:.0f}ms")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_throughput(self, agent_client, response_client):
        """Test throughput"""
        num = 20
        start = time.time()
        
        for i in range(num):
            await agent_client.send_activity(f"Message {i}")
        
        duration = time.time() - start
        throughput = num / duration
        
        assert throughput > 10.0
        print(f"Throughput: {throughput:.1f} req/sec")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_load(self, agent_client, response_client):
        """Test concurrent requests"""
        import asyncio
        
        tasks = [
            agent_client.send_activity(f"Msg {i}")
            for i in range(10)
        ]
        
        await asyncio.gather(*tasks)
        responses = await response_client.pop()
        
        assert len(responses) >= 10
```

## Summary

Performance testing ensures:

1. **Response Time** - Requests complete within acceptable time
2. **Throughput** - Agent handles expected request rate
3. **Reliability** - No degradation under load
4. **Resource Usage** - Efficient memory and CPU usage
5. **Scalability** - Performance scales with load

Key tools:
- **Benchmark CLI** - Load testing via command line
- **Python Tests** - Programmatic performance tests
- **Profiling** - Identify bottlenecks
- **Monitoring** - Track performance over time

---

**Related Guides**:
- [CLI Tools](./CLI_TOOLS.md) - Benchmark command
- [Best Practices](./BEST_PRACTICES.md) - Testing patterns
- [Integration Testing](./INTEGRATION_TESTING.md) - Basic testing
