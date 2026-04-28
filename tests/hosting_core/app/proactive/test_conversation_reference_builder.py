"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest

from microsoft_agents.hosting.core.app.proactive import ConversationReferenceBuilder
from microsoft_agents.hosting.core.app.proactive.conversation_reference_builder import (
    _service_url_for_channel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _buildable(channel_id="msteams", conv_id="conv-1"):
    """Return a builder that can call .build() without Pydantic errors.

    The implementation passes name explicitly to ChannelAccount, so an agent
    with a name must always be present before calling .build().
    """
    return ConversationReferenceBuilder.create(channel_id, conv_id).with_agent(
        "28:app-id", "Bot"
    )


# ---------------------------------------------------------------------------
# _service_url_for_channel
# ---------------------------------------------------------------------------


class TestServiceUrlForChannel:
    def test_teams_returns_smba_url(self):
        assert (
            _service_url_for_channel("msteams")
            == "https://smba.trafficmanager.net/teams/"
        )

    def test_directline_returns_generic_url(self):
        assert (
            _service_url_for_channel("directline")
            == "https://directline.botframework.com/"
        )

    def test_webchat_returns_generic_url(self):
        assert (
            _service_url_for_channel("webchat") == "https://webchat.botframework.com/"
        )

    def test_unknown_channel_uses_pattern(self):
        assert (
            _service_url_for_channel("mychannel")
            == "https://mychannel.botframework.com/"
        )


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestConversationReferenceBuilderCreate:
    def test_create_sets_channel_id(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-123")
        assert builder._channel_id == "msteams"

    def test_create_sets_conversation_id(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-123")
        assert builder._conversation_id == "conv-123"

    def test_create_returns_builder_instance(self):
        result = ConversationReferenceBuilder.create("msteams", "conv-1")
        assert isinstance(result, ConversationReferenceBuilder)


# ---------------------------------------------------------------------------
# create_for_agent()
# ---------------------------------------------------------------------------


class TestConversationReferenceBuilderCreateForAgent:
    def test_create_for_agent_teams_prefixes_id(self):
        builder = ConversationReferenceBuilder.create_for_agent("app-id", "msteams")
        assert builder._agent_id == "28:app-id"

    def test_create_for_agent_non_teams_no_prefix(self):
        builder = ConversationReferenceBuilder.create_for_agent("app-id", "directline")
        assert builder._agent_id == "app-id"

    def test_create_for_agent_default_service_url_teams(self):
        builder = ConversationReferenceBuilder.create_for_agent("app-id", "msteams")
        assert builder._service_url == "https://smba.trafficmanager.net/teams/"

    def test_create_for_agent_custom_service_url(self):
        builder = ConversationReferenceBuilder.create_for_agent(
            "app-id", "msteams", service_url="https://custom.url/"
        )
        assert builder._service_url == "https://custom.url/"

    def test_create_for_agent_returns_builder_instance(self):
        result = ConversationReferenceBuilder.create_for_agent("app-id", "msteams")
        assert isinstance(result, ConversationReferenceBuilder)


# ---------------------------------------------------------------------------
# Fluent setters
# ---------------------------------------------------------------------------


class TestConversationReferenceBuilderSetters:
    def test_with_agent_sets_id_and_name(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_agent("agent-id", "My Agent")
        assert builder._agent_id == "agent-id"
        assert builder._agent_name == "My Agent"

    def test_with_agent_returns_self(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        result = builder.with_agent("agent-id", "Agent")
        assert result is builder

    def test_with_agent_name_optional(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_agent("agent-id")
        assert builder._agent_id == "agent-id"
        assert builder._agent_name is None

    def test_with_user_sets_id_and_name(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_user("user-id", "Alice")
        assert builder._user_id == "user-id"
        assert builder._user_name == "Alice"

    def test_with_user_returns_self(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        result = builder.with_user("user-id", "Alice")
        assert result is builder

    def test_with_service_url_sets_url(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_service_url("https://override/")
        assert builder._service_url == "https://override/"

    def test_with_service_url_returns_self(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        result = builder.with_service_url("https://override/")
        assert result is builder

    def test_with_activity_id_sets_id(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_activity_id("act-123")
        assert builder._activity_id == "act-123"

    def test_with_activity_id_returns_self(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        result = builder.with_activity_id("act-123")
        assert result is builder

    def test_with_locale_sets_locale(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        builder.with_locale("en-US")
        assert builder._locale == "en-US"

    def test_with_locale_returns_self(self):
        builder = ConversationReferenceBuilder.create("msteams", "conv-1")
        result = builder.with_locale("fr-FR")
        assert result is builder


# ---------------------------------------------------------------------------
# build()
# ---------------------------------------------------------------------------


class TestConversationReferenceBuilderBuild:
    def test_build_sets_channel_id(self):
        ref = _buildable().build()
        assert ref.channel_id == "msteams"

    def test_build_sets_conversation_id(self):
        ref = _buildable(conv_id="conv-abc").build()
        assert ref.conversation.id == "conv-abc"

    def test_build_default_service_url_teams(self):
        ref = _buildable("msteams").build()
        assert ref.service_url == "https://smba.trafficmanager.net/teams/"

    def test_build_default_service_url_generic(self):
        ref = _buildable("directline").build()
        assert ref.service_url == "https://directline.botframework.com/"

    def test_build_respects_explicit_service_url(self):
        ref = _buildable().with_service_url("https://custom/").build()
        assert ref.service_url == "https://custom/"

    def test_build_sets_agent_account(self):
        ref = (
            ConversationReferenceBuilder.create("msteams", "conv-1")
            .with_agent("28:app-id", "My Bot")
            .build()
        )
        assert ref.agent.id == "28:app-id"
        assert ref.agent.name == "My Bot"

    def test_build_sets_user_account(self):
        ref = _buildable().with_user("user-oid", "Alice").build()
        assert ref.user.id == "user-oid"
        assert ref.user.name == "Alice"

    def test_build_sets_activity_id(self):
        ref = _buildable().with_activity_id("act-xyz").build()
        assert ref.activity_id == "act-xyz"

    def test_build_sets_locale(self):
        ref = _buildable().with_locale("en-GB").build()
        assert ref.locale == "en-GB"

    def test_build_no_user_when_not_set(self):
        ref = _buildable().build()
        assert ref.user is None

    def test_build_requires_channel_id(self):
        builder = ConversationReferenceBuilder()
        with pytest.raises(ValueError):
            builder.build()

    def test_build_teams_prefix_from_create_for_agent(self):
        builder = ConversationReferenceBuilder.create_for_agent("app-id", "msteams")
        # Provide name: implementation passes it explicitly to ChannelAccount (rejects None)
        builder._agent_name = "Bot"
        # Provide conversation_id: create_for_agent doesn't set it; ConversationAccount.id
        # is NonEmptyString so the "" fallback in build() raises a Pydantic error
        builder._conversation_id = "conv-1"
        ref = builder.build()
        assert ref.agent.id == "28:app-id"

    def test_fluent_chaining_all_methods(self):
        ref = (
            ConversationReferenceBuilder.create("msteams", "conv-1")
            .with_agent("28:app-id", "Bot")
            .with_user("user-id", "Bob")
            .with_locale("de-DE")
            .with_activity_id("act-99")
            .with_service_url("https://override.url/")
            .build()
        )
        assert ref.channel_id == "msteams"
        assert ref.agent.id == "28:app-id"
        assert ref.user.id == "user-id"
        assert ref.locale == "de-DE"
        assert ref.activity_id == "act-99"
        assert ref.service_url == "https://override.url/"
