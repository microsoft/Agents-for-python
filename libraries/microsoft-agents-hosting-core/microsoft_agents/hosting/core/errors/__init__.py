# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents SDK.

This module provides centralized error messages with error codes and help URLs
following the pattern established in the C# SDK.
"""

from .error_message import ErrorMessage
from .error_resources import ErrorResources

# Singleton instance
error_resources = ErrorResources()

__all__ = ["ErrorMessage", "ErrorResources", "error_resources"]
