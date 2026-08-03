"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import logging

logging.warning(
    "The `microsoft-agents-hosting-teams` package is deprecated. "
    "Please start using the `microsoft-agents-hosting-msteams` package "
    "for better support and future updates. "
)

from .teams_activity_handler import TeamsActivityHandler
from .teams_agent_extension import (
    TeamsAgentExtension,
    MessageExtension,
    TaskModule,
    Meeting,
)
from .teams_info import TeamsInfo

__all__ = [
    "TeamsActivityHandler",
    "TeamsAgentExtension",
    "MessageExtension",
    "TaskModule",
    "Meeting",
    "TeamsInfo",
]
