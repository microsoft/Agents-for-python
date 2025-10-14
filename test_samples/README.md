# Setting Up Virtual Environment and installing the SDK

This guide explains how to create and activate a Python virtual environment using `venv` for Python versions 3.10 to 3.11.

## What is a Virtual Environment?

A virtual environment is an isolated Python environment that allows you to install packages for a specific project without affecting your system's global Python installation. This helps avoid package conflicts between different projects.

## Prerequisites

- Python 3.10, or 3.11 installed on your system
- Basic knowledge of command line operations

## Creating a Virtual Environment

### On Linux/macOS

1. Open a terminal window
2. Navigate to your project directory:
   ```bash
   cd the-root-of-this-project
   ```
3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

### On Windows

1. Open Command Prompt or PowerShell
2. Navigate to your project directory:
   ```
   cd the-root-of-this-project
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   ```

## Activating the Virtual Environment

### On Linux/macOS

```bash
source venv/bin/activate
```

### On Windows

#### Command Prompt
```
venv\Scripts\activate.bat
```

#### PowerShell
```
venv\Scripts\Activate.ps1
```

Once activated, you'll notice your command prompt changes to show the name of the activated environment. For example:
```
(venv) $
```

## Deactivating the Virtual Environment

When you're done working in the virtual environment, you can deactivate it by running:

```bash
deactivate
```

## Verifying Python Version

To verify the Python version in your virtual environment:

```bash
python --version
```

Make sure it shows a version at least 3.10 

## Installing Test Packages

After activating your virtual environment, you can install packages from pypi test (the test index will be replaced with the regular index before going out of preview):

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-activity
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-authorization
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-connector
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-client
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-hosting-core
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-authentication-msal
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-copilotstudio-client
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-hosting-core-aiohttp
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ microsoft-agents-storage-core
```