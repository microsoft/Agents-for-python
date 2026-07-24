# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for TeamsAgentExtension property accessors and top-level wrapping."""

import pytest

from .helpers import _make_app, is_supported_version

pytestmark = pytest.mark.skipif(
    not is_supported_version,
    reason="microsoft-agents-hosting-teams tests require Python 3.11+",
)

if is_supported_version:
    from microsoft_agents.activity import Activity, Channels
    from microsoft_teams.api import ApiClient
    from microsoft_teams.api.models import ChannelData

    from microsoft_agents.hosting.msteams import TeamsAgentExtension
    from microsoft_agents.hosting.msteams.channel import Channel
    from microsoft_agents.hosting.msteams.config import Config
    from microsoft_agents.hosting.msteams.file_consent import FileConsent
    from microsoft_agents.hosting.msteams.meeting import Meeting
    from microsoft_agents.hosting.msteams.message import Message
    from microsoft_agents.hosting.msteams.message_extension import MessageExtension
    from microsoft_agents.hosting.msteams.task_module import TaskModule
    from microsoft_agents.hosting.msteams.team import Team


class _FakeServiceSet:
    def __init__(self):
        self._state = {}

    def has(self, key):
        return key in self._state

    def set(self, key, value):
        self._state[key] = value


class _FakeContext:
    """Minimal context stand-in for exercising the before_turn hook directly."""

    def __init__(self, activity, identity=None):
        self.activity = activity
        self.identity = identity
        self.services = _FakeServiceSet()


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


class TestBeforeTurnHook:

    def setup_method(self):
        self.app = _make_app()
        self.ext = TeamsAgentExtension(self.app)
        # The extension registers exactly one before_turn hook during construction.
        self.hook = self.app.before_turn.call_args[0][0]

    def test_hook_is_registered(self):
        self.app.before_turn.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_teams_channel_is_untouched(self):
        activity = Activity(
            type="message", channel_id="webchat", channel_data={"channel": {"id": "c"}}
        )
        ctx = _FakeContext(activity)

        result = await self.hook(ctx, None)

        assert result is True
        # channel_data left as the raw dict; no Teams API client cached
        assert activity.channel_data == {"channel": {"id": "c"}}
        assert not ctx.services.has(ApiClient)

    @pytest.mark.asyncio
    async def test_teams_channel_deserializes_channel_data(self):
        activity = Activity(
            type="conversationUpdate",
            channel_id=Channels.ms_teams,
            service_url="https://smba.trafficmanager.net/teams/",
            channel_data={"channel": {"id": "c1"}},
        )
        ctx = _FakeContext(activity, identity=None)

        result = await self.hook(ctx, None)

        assert result is True
        assert isinstance(activity.channel_data, ChannelData)
        assert activity.channel_data.channel.id == "c1"
        assert ctx.services.has(ApiClient)

    @pytest.mark.asyncio
    async def test_teams_channel_without_channel_data_sets_none(self):
        activity = Activity(
            type="conversationUpdate",
            channel_id=Channels.ms_teams,
            service_url="https://smba.trafficmanager.net/teams/",
        )
        ctx = _FakeContext(activity, identity=None)

        result = await self.hook(ctx, None)

        assert result is True
        assert activity.channel_data is None
