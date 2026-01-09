# CLI Tools Guide

Master the command-line interface for the Microsoft Agents Testing Framework.

## Overview

The `aclip` command provides powerful CLI tools for testing, authentication, and benchmarking:

```
aclip [global-options] <command> [command-options]
```

## Global Options

These options work with any command:

```bash
# Specify environment file
--env_path .env

# Enable verbose logging
--verbose

# Set custom service URL
--service_url http://localhost:8001/
```

## Commands

### 1. Data-Driven Testing (ddt)

Run YAML-based declarative tests without writing Python code.

#### Basic Usage

```bash
aclip --env_path .env ddt ./tests/scenarios.yaml
```

#### Full Example

```bash
aclip \
  --env_path .env \
  ddt ./tests/scenarios.yaml \
  --service_url http://localhost:8001/ \
  --pytest-args "-v -s"
```

#### Options

| Option | Description | Example |
|--------|-------------|---------|
| `<path>` | Path to YAML test file | `./tests/test.yaml` |
| `--service_url` | Response service URL | `http://localhost:8001/` |
| `--pytest-args` | Arguments for pytest | `"-v -s"` |

#### YAML File Format

```yaml
# tests/my_tests.yaml
name: "My Test Suite"
scenarios:
  - name: "Greeting Test"
    send:
      type: "message"
      text: "Hello"
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Complex Test"
    send:
      type: "message"
      text: "What's 2+2?"
      locale: "en-US"
    assert:
      - type: "contains"
        path: "text"
        value: "4"
```

#### Example Workflow

```bash
# Create test file
cat > tests/greetings.yaml << 'EOF'
name: "Greeting Tests"
scenarios:
  - name: "Simple Greeting"
    send:
      type: "message"
      text: "Hi"
    assert:
      - type: "exists"
        path: "text"
EOF

# Run tests
aclip --env_path .env ddt ./tests/greetings.yaml -v
```

### 2. Authentication Server

Run a local authentication test server for development and testing.

#### Basic Usage

```bash
aclip --env_path .env auth --port 3978
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--port` | int | 3978 | Port for server |

#### Full Example

```bash
# Start auth server on port 5000
aclip --env_path .env auth --port 5000

# In another terminal, test the server
curl http://localhost:5000/ping
```

#### Use Cases

- **Development**: Test auth locally without Azure
- **CI/CD**: Simulate Bot Framework auth
- **Debugging**: Verify token generation
- **Integration**: Test OAuth flows

#### What It Does

The auth server:
- Generates OAuth tokens
- Validates credentials
- Simulates Bot Framework endpoints
- Handles token refresh

### 3. Post Activity

Send a single activity to your agent for testing.

#### Basic Usage

```bash
aclip --env_path .env post --payload_path ./payload.json
```

#### Full Example

```bash
# Send activity with payload
aclip \
  --env_path .env \
  post \
  --payload_path ./payload.json \
  --verbose
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--payload_path` | `-p` | str | `./payload.json` | Path to payload JSON |
| `--verbose` | `-v` | flag | False | Enable verbose output |
| `--async_mode` | `-a` | flag | False | Use async workers |

#### Payload Format

Create `payload.json`:

```json
{
  "type": "message",
  "text": "Hello agent!",
  "from": {
    "id": "user123",
    "name": "Test User"
  },
  "conversation": {
    "id": "conv123"
  },
  "channelId": "directline"
}
```

#### Example Workflow

```bash
# Create payload
cat > payload.json << 'EOF'
{
  "type": "message",
  "text": "Hello!",
  "from": {"id": "user1", "name": "Tester"},
  "conversation": {"id": "conv1"},
  "channelId": "directline"
}
EOF

# Send it
aclip --env_path .env post -p ./payload.json -v

# Output example:
# Sending activity...
# Activity sent successfully
# Response: {...}
```

### 4. Benchmark

Run performance tests with concurrent workers to stress-test your agent.

#### Basic Usage

```bash
aclip --env_path .env benchmark --payload_path ./payload.json --num_workers 10
```

#### Full Example

```bash
aclip \
  --env_path .env \
  benchmark \
  --payload_path ./payload.json \
  --num_workers 10 \
  --verbose \
  --async_mode
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--payload_path` | `-p` | str | `./payload.json` | Payload file |
| `--num_workers` | `-n` | int | 1 | Number of workers |
| `--verbose` | `-v` | flag | False | Verbose output |
| `--async_mode` | `-a` | flag | False | Async workers |

#### Understanding Benchmark Results

Example output:

```
Starting benchmark with 10 workers...

=== Results ===
Total Requests: 10
Successful: 10
Failed: 0

=== Timing (seconds) ===
Min: 0.234
Max: 0.892
Mean: 0.512
Median: 0.498

=== Throughput ===
Requests/second: 19.5

=== Status ===
Success Rate: 100%
```

#### Benchmark Workflow

```bash
# Create payload for benchmark
cat > bench_payload.json << 'EOF'
{
  "type": "message",
  "text": "Test message",
  "from": {"id": "user", "name": "Tester"},
  "conversation": {"id": "conv"},
  "channelId": "directline"
}
EOF

# Run small test (1 worker)
aclip --env_path .env benchmark -p ./bench_payload.json -n 1

# Run moderate load (10 workers)
aclip --env_path .env benchmark -p ./bench_payload.json -n 10 -v

# Run heavy load (100 workers, async)
aclip --env_path .env benchmark -p ./bench_payload.json -n 100 -a -v
```

#### Interpreting Results

| Metric | What It Means | Good Range |
|--------|---------------|-----------|
| **Min/Max** | Fastest/slowest response | Small range = consistent |
| **Mean** | Average response time | <500ms for most agents |
| **Median** | Middle value (robust avg) | Close to mean = consistent |
| **Success Rate** | % requests succeeded | 100% = no errors |

## Practical Examples

### Example 1: Test Flow with Multiple Commands

```bash
# Step 1: Start auth server in background
aclip --env_path .env auth --port 3978 &

# Step 2: Send test activity
aclip --env_path .env post -p ./payload.json -v

# Step 3: Run small benchmark
aclip --env_path .env benchmark -p ./payload.json -n 5

# Step 4: Run full DDT suite
aclip --env_path .env ddt ./tests/ -v
```

### Example 2: CI/CD Pipeline

```bash
#!/bin/bash
# ci_test.sh

set -e  # Exit on error

ENV_FILE=".env.test"

echo "Running integration tests..."
aclip --env_path $ENV_FILE ddt ./tests/integration.yaml -v

echo "Running benchmark..."
aclip --env_path $ENV_FILE benchmark -p ./payload.json -n 50

echo "All tests passed!"
```

### Example 3: Local Development

```bash
# Terminal 1: Start auth server
aclip --env_path .env auth --port 3978

# Terminal 2: Watch and run tests
while inotifywait -e modify tests/; do
  aclip --env_path .env ddt ./tests/ -v
done
```

### Example 4: Performance Baseline

```bash
# Create different payloads
cat > payloads/simple.json << 'EOF'
{"type": "message", "text": "Hi"}
EOF

cat > payloads/complex.json << 'EOF'
{"type": "message", "text": "Complex question with long text"}
EOF

# Benchmark both
echo "Simple payload:"
aclip --env_path .env benchmark -p ./payloads/simple.json -n 100 -v

echo "Complex payload:"
aclip --env_path .env benchmark -p ./payloads/complex.json -n 100 -v

# Compare results
```

## Troubleshooting CLI

### Issue: Command Not Found

```
aclip: command not found
```

**Solution**:
```bash
# Verify installation
pip install microsoft-agents-testing

# Verify in path
which aclip
python -m microsoft_agents.testing.cli --version
```

### Issue: Connection Refused

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solution**:
```bash
# Check if agent is running
curl http://localhost:3978/

# Check auth server
curl http://localhost:8001/

# Start missing services
aclip --env_path .env auth --port 3978
```

### Issue: Invalid Payload

```
JSONDecodeError: Expecting value: line 1 column 1
```

**Solution**:
```bash
# Validate JSON
python -m json.tool payload.json

# Create valid payload
cat > payload.json << 'EOF'
{
  "type": "message",
  "text": "test"
}
EOF
```

### Issue: Environment Variables Missing

```
KeyError: 'CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID'
```

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify content
cat .env

# Create if missing
cat > .env << 'EOF'
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=<your-id>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=<your-tenant>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=<your-secret>
EOF
```

## Advanced Usage

### Custom YAML Tests

Create reusable test scenarios:

```yaml
name: "Advanced Agent Tests"

# Shared test data
defaults:
  type: "message"
  channelId: "directline"

scenarios:
  - name: "Test with defaults"
    send:
      text: "Hello"
      # Inherits: type, channelId from defaults
    assert:
      - type: "exists"
        path: "text"
  
  - name: "Test with custom"
    send:
      type: "invoke"
      name: "custom_invoke"
    assert:
      - type: "exists"
        path: "value"
```

### Scripted Benchmarking

```bash
#!/bin/bash
# run_benchmarks.sh

WORKERS=(5 10 25 50 100)

echo "Worker Scaling Benchmark"
echo "========================"

for n in "${WORKERS[@]}"; do
  echo "Workers: $n"
  aclip --env_path .env benchmark \
    -p ./payload.json \
    -n $n \
    | grep "Requests/second"
done
```

## Summary

| Command | Purpose | Example |
|---------|---------|---------|
| **ddt** | Run YAML tests | `aclip ddt test.yaml` |
| **auth** | Start auth server | `aclip auth --port 3978` |
| **post** | Send activity | `aclip post -p payload.json` |
| **benchmark** | Performance test | `aclip benchmark -p payload.json -n 100` |

---

**Next Steps**:
- [Data-Driven Testing](./DATA_DRIVEN_TESTING.md) - YAML format details
- [Performance Testing](./PERFORMANCE_TESTING.md) - Benchmarking guide
- [Best Practices](./BEST_PRACTICES.md) - CLI best practices
