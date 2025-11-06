# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Hosting Teams package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import TeamsErrorResources

# Singleton instance
teams_errors = TeamsErrorResources()

__all__ = ["ErrorMessage", "TeamsErrorResources", "teams_errors"]
