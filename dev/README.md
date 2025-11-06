# Development Tools

This directory contains development tools and utilities for the Microsoft Agents for Python project.

## Contents

- [`install.sh`](install.sh) - Installation script for development dependencies
- [`benchmark/`](benchmark/) - Performance benchmarking tools
- [`microsoft-agents-testing/`](microsoft-agents-testing/) - Testing framework package

## Quick Setup

To set up the development environment, run the installation script:

```bash
./install.sh
```

This script installs the testing framework package in editable mode, allowing you to make changes and test them immediately.

## Benchmarking

The [`benchmark/`](benchmark/) directory contains tools for performance testing and stress testing agents. See the [benchmark README](benchmark/README.md) for detailed setup and usage instructions.

### Key Features:
- Support for both standard Python and free-threaded Python 3.13+
- Configurable worker threads for stress testing
- Token-based authentication for realistic testing scenarios
- Basic payload sending stress tests

### Quick Start:
1. Navigate to the benchmark directory
2. Set up a Python virtual environment
3. Configure authentication settings in `.env` (use `env.template` as a reference)
4. Run tests with `python -m src.main --num_workers=<number>`

## Testing Framework

The [`microsoft-agents-testing/`](microsoft-agents-testing/) directory contains a specialized testing framework for Microsoft Agents. This package provides:

- Testing utilities and helpers
- Mock objects and test fixtures
- Integration testing tools

The package can be installed in editable mode using the provided installation script, making it easy to develop and test changes.

## Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)
- For benchmarking: Valid Azure Bot Service credentials

## Development Workflow

1. Install development dependencies using `./install.sh`
2. Make changes to the testing framework or benchmark tools
3. Test your changes using the benchmark tools
4. Run the full test suite to ensure compatibility

## Notes

- The benchmark tool currently uses threading rather than async coroutines
- Free-threaded Python 3.13+ support is available for improved performance
- All tools require proper authentication configuration for realistic testing