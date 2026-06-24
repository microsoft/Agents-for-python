# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension property accessors and top-level wrapping."""

import pytest

from .helpers import _make_app, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.12+",
)

if is_supported_version:
    from microsoft_agents.hosting.msteams import TeamsAgentExtension
    from microsoft_agents.hosting.msteams.channel import Channel
    from microsoft_agents.hosting.msteams.config import Config
    from microsoft_agents.hosting.msteams.file_consent import FileConsent
    from microsoft_agents.hosting.msteams.meeting import Meeting
    from microsoft_agents.hosting.msteams.message import Message
    from microsoft_agents.hosting.msteams.message_extension import MessageExtension
    from microsoft_agents.hosting.msteams.task_module import TaskModule
    from microsoft_agents.hosting.msteams.team import Team


class TestTeamsAgentExtensionProperties:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)

    def test_channels_property_returns_channel(self):
        assert isinstance(self.ext.channels, Channel)

    def test_config_property_returns_config(self):
        assert isinstance(self.ext.config, Config)

    def test_file_consent_property_returns_file_consent(self):
        assert isinstance(self.ext.file_consent, FileConsent)

    def test_meetings_property_returns_meeting(self):
        assert isinstance(self.ext.meetings, Meeting)

    def test_messages_property_returns_message(self):
        assert isinstance(self.ext.messages, Message)

    def test_message_extensions_property_returns_message_extension(self):
        assert isinstance(self.ext.message_extensions, MessageExtension)

    def test_task_modules_property_returns_task_module(self):
        assert isinstance(self.ext.task_modules, TaskModule)

    def test_teams_property_returns_team(self):
        assert isinstance(self.ext.teams, Team)

    def test_properties_return_same_instance_each_call(self):
        assert self.ext.channels is self.ext.channels
        assert self.ext.meetings is self.ext.meetings
        assert self.ext.message_extensions is self.ext.message_extensions
        assert self.ext.task_modules is self.ext.task_modules
