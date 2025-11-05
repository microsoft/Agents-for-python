# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Authentication MSAL package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import AuthenticationErrorResources

# Singleton instance
authentication_errors = AuthenticationErrorResources()

__all__ = ["ErrorMessage", "AuthenticationErrorResources", "authentication_errors"]
