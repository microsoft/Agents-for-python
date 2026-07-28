# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for the Microsoft Agents Entra ID Auth Sidecar package.
"""

from .error_resources import (
    SidecarAuthError,
    SidecarUnavailableError,
    SidecarConfigurationError,
)

__all__ = [
    "SidecarAuthError",
    "SidecarUnavailableError",
    "SidecarConfigurationError",
]
