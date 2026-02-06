# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Microsoft Agents Testing CLI.

This package provides command-line tools for testing and interacting
with M365 Agents SDK for Python.

Structure:
    - config/: Configuration loading and management
    - core/: Reusable utilities (executors, output formatting, decorators)
    - commands/: Individual CLI commands
    - main.py: CLI entry point
"""

from .main import main

__all__ = [ "main" ]