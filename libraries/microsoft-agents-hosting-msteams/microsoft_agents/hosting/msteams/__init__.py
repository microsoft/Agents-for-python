"""
Microsoft Agents Hosting Teams package.

Provides Teams-specific activity handlers, extensions, and utilities for building
Microsoft Teams bots and agents using the AgentApplication or ActivityHandler models.
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

from .teams_api_client import get_teams_api_client

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
    "get_teams_api_client",
]
