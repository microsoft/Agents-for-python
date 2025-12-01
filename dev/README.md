# Development Tools

DISCLAIMER: the content of this directory is experimental and not meant for production use.

Development utilities for the Microsoft Agents for Python project.

## Contents

- **[`install.sh`](install.sh)** - Installs testing framework in editable mode
- **[`benchmark/`](benchmark/)** - Performance testing and stress testing tools  
- **[`microsoft-agents-testing/`](microsoft-agents-testing/)** - Testing framework package

## Quick Setup

```bash
pip install -e ./microsoft-agents-testing/ --config-settings editable_mode=compat
```

## Benchmarking

Performance testing tools with support for concurrent workers and authentication. Requires a running agent instance and Azure Bot Service credentials.

See [benchmark/README.md](benchmark/README.md) for setup and usage details.

## Testing Framework

Provides testing utilities and helpers for Microsoft Agents development. Installed in editable mode for active development.