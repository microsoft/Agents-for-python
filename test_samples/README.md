# Setting Up Virtual Environment and installing the SDK

This guide explains how to create and activate a Python virtual environment using `venv` for Python versions 3.10 to 3.14.

## What is a Virtual Environment?

A virtual environment is an isolated Python environment that allows you to install packages for a specific project without affecting your system's global Python installation. This helps avoid package conflicts between different projects.

## Prerequisites

- Python 3.10, 3.11, 3.12, 3.13, or 3.14 installed on your system
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

Make sure it shows a version of at least 3.10.

## Installing Test Packages

After activating your virtual environment, you can install packages from pypi:

```bash
pip install microsoft-agents-activity
pip install microsoft-agents-authorization
pip install microsoft-agents-connector
pip install microsoft-agents-client
pip install microsoft-agents-hosting-core
pip install microsoft-agents-authentication-msal
pip install microsoft-agents-copilotstudio-client
pip install microsoft-agents-hosting-core-aiohttp
pip install microsoft-agents-storage-core
```