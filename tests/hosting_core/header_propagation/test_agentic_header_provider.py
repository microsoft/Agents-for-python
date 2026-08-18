# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Tests for AgenticHeaderProvider and HeaderPropagationContext."""

import pytest

from microsoft_agents.activity import Activity, RoleTypes
from microsoft_agents.activity.channel_account import ChannelAccount
from microsoft_agents.hosting.core.header_propagation import (
    AgenticHeaderProvider,
    HeaderPropagationContext,
)


def _agentic_activity(
    role=RoleTypes.agentic_user,
    agentic_app_id="Entra:test-guid-1234",
    channel_id="msteams",
) -> Activity:
    return Activity(
        type="message",
        recipient=ChannelAccount(role=role, agentic_app_id=agentic_app_id),
        channel_id=channel_id,
    )


class TestAgenticHeaderProvider:
    def test_agentic_request_emits_all_headers(self):
        provider = AgenticHeaderProvider(_agentic_activity(), "MyTestAgent")

        headers = provider.get_headers()

        assert headers == {
            "AgentRegistrar": "A365",
            "AgentID": "Entra:test-guid-1234",
            "AgentName": "MyTestAgent",
            "Agent-Referrer": "msteams",
        }

    def test_agentic_identity_role_emits_headers(self):
        provider = AgenticHeaderProvider(
            _agentic_activity(
                role=RoleTypes.agentic_identity,
                agentic_app_id="Entra:identity-guid",
                channel_id="webchat",
            ),
            "IdentityAgent",
        )

        headers = provider.get_headers()

        assert headers["AgentRegistrar"] == "A365"
        assert headers["AgentID"] == "Entra:identity-guid"
        assert headers["AgentName"] == "IdentityAgent"
        assert headers["Agent-Referrer"] == "webchat"

    def test_sub_channel_is_preserved_in_referrer(self):
        provider = AgenticHeaderProvider(
            _agentic_activity(channel_id="msteams:Copilot"), "TestAgent"
        )

        assert provider.get_headers()["Agent-Referrer"] == "msteams:Copilot"

    def test_non_agentic_request_emits_no_headers(self):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(role=RoleTypes.user),
            channel_id="msteams",
        )

        assert AgenticHeaderProvider(activity, "MyAgent").get_headers() == {}

    def test_missing_role_emits_no_headers(self):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(),
            channel_id="msteams",
        )

        assert AgenticHeaderProvider(activity, "MyAgent").get_headers() == {}

    def test_missing_agentic_app_id_yields_empty_string(self):
        provider = AgenticHeaderProvider(
            _agentic_activity(agentic_app_id=None), "MyAgent"
        )

        assert provider.get_headers()["AgentID"] == ""

    def test_none_activity_raises(self):
        with pytest.raises(ValueError):
            AgenticHeaderProvider(None, "MyAgent")


class TestHeaderPropagationContext:
    def setup_method(self):
        HeaderPropagationContext.reset()

    def test_collect_headers_applies_provider_headers(self):
        activity = _agentic_activity(
            agentic_app_id="Entra:app-id-123", channel_id="msteams:Copilot"
        )
        HeaderPropagationContext.register(AgenticHeaderProvider(activity, "TestAgent"))

        headers = HeaderPropagationContext.collect_headers()

        assert headers == {
            "AgentRegistrar": "A365",
            "AgentID": "Entra:app-id-123",
            "AgentName": "TestAgent",
            "Agent-Referrer": "msteams:Copilot",
        }

    def test_collect_headers_non_agentic_adds_nothing(self):
        activity = Activity(
            type="message",
            recipient=ChannelAccount(role=RoleTypes.user),
            channel_id="msteams",
        )
        HeaderPropagationContext.register(AgenticHeaderProvider(activity, "TestAgent"))

        assert HeaderPropagationContext.collect_headers() == {}

    def test_reset_clears_registered_providers(self):
        HeaderPropagationContext.register(
            AgenticHeaderProvider(_agentic_activity(), "TestAgent")
        )
        HeaderPropagationContext.reset()

        assert HeaderPropagationContext.providers() == []
        assert HeaderPropagationContext.collect_headers() == {}
