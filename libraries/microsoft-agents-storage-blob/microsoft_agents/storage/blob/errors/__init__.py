# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Storage Blob package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import BlobStorageErrorResources

# Singleton instance
blob_storage_errors = BlobStorageErrorResources()

__all__ = ["ErrorMessage", "BlobStorageErrorResources", "blob_storage_errors"]
