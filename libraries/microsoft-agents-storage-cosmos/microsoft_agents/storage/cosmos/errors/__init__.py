# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Storage Cosmos package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import StorageErrorResources

# Singleton instance
storage_errors = StorageErrorResources()

__all__ = ["ErrorMessage", "StorageErrorResources", "storage_errors"]
