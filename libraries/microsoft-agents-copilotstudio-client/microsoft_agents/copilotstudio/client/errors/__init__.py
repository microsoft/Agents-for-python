# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Error resources for Microsoft Agents Copilot Studio Client package.
"""

from microsoft_agents.hosting.core.errors import ErrorMessage

from .error_resources import CopilotStudioErrorResources

# Singleton instance
copilot_studio_errors = CopilotStudioErrorResources()

__all__ = ["ErrorMessage", "CopilotStudioErrorResources", "copilot_studio_errors"]
