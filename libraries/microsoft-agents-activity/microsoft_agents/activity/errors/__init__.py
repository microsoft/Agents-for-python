# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Activity package.
"""

from .error_message import ErrorMessage
from .error_resources import ActivityErrorResources, ConfigurationErrorResources

# Singleton instance
activity_errors = ActivityErrorResources()
configuration_errors = ConfigurationErrorResources()

__all__ = [
    "ErrorMessage",
    "ActivityErrorResources",
    "ConfigurationErrorResources",
    "activity_errors",
    "configuration_errors",
]
