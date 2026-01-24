# Installation & Setup Guide

Complete instructions for installing and configuring the Microsoft Agents Testing Framework.

## System Requirements

### Minimum Requirements
- **Python**: 3.10 or later
- **OS**: Windows, macOS, or Linux
- **Disk Space**: 200 MB for installation
- **Memory**: 2 GB minimum (4 GB recommended)

### Optional Requirements (for some features)
- **Docker**: For containerized testing (optional)
- **Git**: For cloning sample repositories
- **Azure Account**: For Bot Framework credentials (optional)

## Installation Methods

### Method 1: Standard Installation (Recommended)

```bash
# Basic installation
pip install microsoft-agents-testing

# Verify installation
python -c "import microsoft_agents.testing; print('✓ Installed successfully')"
```

### Method 2: With Development Tools

```bash
# Install with development dependencies
pip install microsoft-agents-testing[dev]

# Includes: pytest, pytest-asyncio, black, flake8, mypy
```

### Method 3: From Source (Development)

```bash
# Clone the repository
git clone https://github.com/microsoft/Agents.git
cd Agents/python/dev/microsoft-agents-testing

# Install in editable mode
pip install -e . --config-settings editable_mode=compat
```

### Method 4: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the package
pip install microsoft-agents-testing
```

## Configuration

### Step 1: Create Environment File

Create a `.env` file in your project root:

```env
# ============================================================
# REQUIRED: Azure Bot Service Credentials
# ============================================================

# Service Connection Settings
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID=<your-app-id>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__TENANTID=<your-tenant-id>
CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTSECRET=<your-app-secret>

# ============================================================
# OPTIONAL: Agent URLs
# ============================================================

# Your agent's endpoint
AGENT_URL=http://localhost:3978/

# Mock response service endpoint
SERVICE_URL=http://localhost:8001/

# ============================================================
# OPTIONAL: Additional Settings
# ============================================================

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Request timeout (seconds)
REQUEST_TIMEOUT=30

# Response wait timeout (seconds)
RESPONSE_TIMEOUT=5
```

### Step 2: Obtain Azure Credentials

#### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Search for "Bot Service"
3. Create a new Bot Resource or select existing
4. Go to "Configuration" → "Manage password"
5. Copy your **App ID** and create a new **Client Secret**
6. Copy these values to your `.env` file

#### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# List bot resources
az bot show --resource-group <group> --name <bot-name>

# Create new app registration
az ad app create --display-name "MyAgent" --password <password>
```

### Step 3: Verify Configuration

```python
# save as verify_config.py
from microsoft_agents.testing import SDKConfig

config = SDKConfig(env_path=".env")
print("✓ Configuration loaded successfully")
print(f"Client ID: {config.config.get('CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID')}")
```

Run it:
```bash
python verify_config.py
```

## Project Structure Setup

### Recommended Directory Layout

```
my_agent/
├── .env                              # Configuration file
├── .gitignore                        # Don't commit .env!
├── agent/                            # Your agent code
│   ├── __init__.py
│   ├── main.py
│   ├── handlers/
│   │   ├── message_handler.py
│   │   └── invoke_handler.py
│   └── models/
│       └── domain_models.py
├── tests/                            # Test directory
│   ├── __init__.py
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── test_integration.py          # Your integration tests
│   ├── test_unit.py                 # Unit tests (optional)
│   ├── scenarios/                   # DDT YAML files
│   │   ├── greeting_tests.yaml
│   │   ├── error_handling.yaml
│   │   └── advanced_flows.yaml
│   └── fixtures/                    # Test data
│       ├── sample_activities.json
│       └── expected_responses.json
├── docs/                            # Documentation
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Project dependencies
└── README.md                         # Project readme
```

### Create conftest.py for Shared Fixtures

```python
# tests/conftest.py
import pytest
from microsoft_agents.testing import SDKConfig

@pytest.fixture
def config():
    """Load configuration from .env"""
    return SDKConfig(env_path=".env")

@pytest.fixture
def agent_url():
    """Get agent URL from environment"""
    config = SDKConfig(env_path=".env")
    return config.config.get("AGENT_URL", "http://localhost:3978/")

@pytest.fixture
def service_url():
    """Get service URL from environment"""
    config = SDKConfig(env_path=".env")
    return config.config.get("SERVICE_URL", "http://localhost:8001/")
```

## IDE Configuration

### VS Code Setup

Create `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.linting.pylintEnabled": true,
    "python.linting.pylintArgs": [
        "--max-line-length=120"
    ],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.python"
    }
}
```

### PyCharm Setup

1. Go to **Settings** → **Project** → **Python Interpreter**
2. Select your virtual environment
3. Go to **Settings** → **Tools** → **Python Integrated Tools**
4. Set **Default test runner** to **pytest**

## Pytest Configuration

Create `pytest.ini`:

```ini
[pytest]
# Minimum version
minversion = 7.0

# Test discovery patterns
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# Async support
asyncio_mode = auto

# Markers for test categorization
markers =
    integration: marks tests as integration tests (deselect with '-m "not integration"')
    unit: marks tests as unit tests
    performance: marks tests as performance tests
    slow: marks tests as slow (deselect with '-m "not slow"')

# Coverage options
addopts = 
    -v
    --tb=short
    --strict-markers

# Test paths
testpaths = tests

# Timeout (seconds)
timeout = 300
```

## Dependency Management

### Using requirements.txt

```txt
# requirements.txt
microsoft-agents-testing>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.20.0
python-dotenv>=1.0.0
aiohttp>=3.8.0
```

Install:
```bash
pip install -r requirements.txt
```

### Using pyproject.toml

```toml
[project]
name = "my-agent-tests"
version = "1.0.0"
dependencies = [
    "microsoft-agents-testing>=1.0.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.20.0",
]

[project.optional-dependencies]
dev = [
    "black>=22.0.0",
    "flake8>=4.0.0",
    "mypy>=0.950",
    "pytest-cov>=3.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

## Docker Setup (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Run tests
CMD ["pytest", "tests/", "-v"]
```

Build and run:
```bash
docker build -t my-agent-tests .
docker run my-agent-tests
```

## Verifying Installation

### Quick Verification

```bash
# Check Python version
python --version  # Should be 3.10+

# Check package installation
pip list | grep microsoft-agents

# Test import
python -c "from microsoft_agents.testing import Integration; print('✓ OK')"
```

### Complete Verification Script

```python
# verify_setup.py
import sys
import subprocess

def verify_setup():
    checks = {
        "Python >= 3.10": sys.version_info >= (3, 10),
    }
    
    # Check imports
    imports = [
        "microsoft_agents.testing",
        "pytest",
        "aiohttp",
    ]
    
    for module in imports:
        try:
            __import__(module)
            checks[f"{module}"] = True
        except ImportError:
            checks[f"{module}"] = False
    
    # Print results
    print("Installation Verification Results:")
    print("-" * 40)
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check}")
    
    # Overall status
    all_passed = all(checks.values())
    print("-" * 40)
    print(f"Overall: {'✓ Ready!' if all_passed else '✗ Issues found'}")
    
    return all_passed

if __name__ == "__main__":
    verify_setup()
```

Run it:
```bash
python verify_setup.py
```

## Troubleshooting Installation

### Issue: Module Not Found

```
ModuleNotFoundError: No module named 'microsoft_agents'
```

**Solution**:
```bash
# Make sure package is installed
pip install microsoft-agents-testing

# Verify installation
pip show microsoft-agents-testing
```

### Issue: Wrong Python Version

```
ERROR: microsoft-agents-testing requires Python >= 3.10
```

**Solution**:
```bash
# Check your Python version
python --version

# Use Python 3.10+ (example with pyenv)
pyenv install 3.11.0
pyenv local 3.11.0
```

### Issue: Incompatible Dependencies

```
ERROR: pip's dependency resolver does not currently take into account...
```

**Solution**:
```bash
# Clean install in fresh virtual environment
python -m venv venv_fresh
source venv_fresh/bin/activate
pip install --upgrade pip
pip install microsoft-agents-testing
```

## Upgrading Framework

```bash
# Check current version
pip show microsoft-agents-testing

# Upgrade to latest
pip install --upgrade microsoft-agents-testing

# Upgrade to specific version
pip install microsoft-agents-testing==1.2.0

# Show available versions
pip index versions microsoft-agents-testing
```

## Next Steps

Now that you're set up:

1. **Quick Start**: Read [QUICK_START.md](./QUICK_START.md)
2. **First Test**: Follow [Integration Testing Guide](./INTEGRATION_TESTING.md)
3. **Configure IDE**: Set up your editor with the guides above
4. **Run Tests**: Execute your first test with pytest

---

**Need help?** Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) or create an issue on GitHub.
