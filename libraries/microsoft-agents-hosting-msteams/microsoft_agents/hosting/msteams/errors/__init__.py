# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Teams error resource exports for the Microsoft Agents hosting package."""

from microsoft_agents.activity.errors import ErrorMessage

from .error_resources import TeamsErrorResources

# Shared Teams error resource instance.
teams_errors = TeamsErrorResources()

__all__ = ["ErrorMessage", "TeamsErrorResources", "teams_errors"]
