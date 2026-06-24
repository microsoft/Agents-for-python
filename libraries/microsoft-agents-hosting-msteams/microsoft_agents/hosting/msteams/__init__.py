# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Microsoft 365 Agents SDK -- Microsoft Teams hosting extension.

This package layers Teams-specific functionality on top of an
:class:`~microsoft_agents.hosting.core.AgentApplication`. Its entry point is
:class:`TeamsAgentExtension`, which exposes namespaced route registration for
Teams events (channels, teams, meetings, messages, message extensions, task
modules, configuration, and file consent). It also provides the Teams-aware
:class:`TeamsTurnContext` and :class:`TeamsActivity` helpers.
"""

from .teams_agent_extension import TeamsAgentExtension
from .channel import Channel
from .config import Config
from .file_consent import FileConsent
from .meeting import Meeting
from .message import Message
from .message_extension import MessageExtension
from .task_module import TaskModule
from .team import Team

from .teams_activity import TeamsActivity
from .teams_turn_context import TeamsTurnContext

__all__ = [
    "TeamsAgentExtension",
    "Channel",
    "Config",
    "FileConsent",
    "Meeting",
    "Message",
    "MessageExtension",
    "TaskModule",
    "Team",
    "TeamsActivity",
    "TeamsTurnContext",
]
