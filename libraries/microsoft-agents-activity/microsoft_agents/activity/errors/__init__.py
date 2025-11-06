# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Activity package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import ActivityErrorResources

# Singleton instance
activity_errors = ActivityErrorResources()

__all__ = ["ErrorMessage", "ActivityErrorResources", "activity_errors"]
