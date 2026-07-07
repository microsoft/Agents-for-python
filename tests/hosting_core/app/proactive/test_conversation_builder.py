"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest

from microsoft_agents.hosting.core.app.proactive import (
    Conversation,
    ConversationBuilder,
)
from microsoft_agents.hosting.core.authorization import ClaimsIdentity

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _prep_build(builder: ConversationBuilder) -> ConversationBuilder:
    """Make a ConversationBuilder ready to call .build() without Pydantic errors.

    The implementation passes _agent_name and _conversation_id directly to
    Pydantic models that reject None / empty-string values.  There is no public
    API to set these on the builder, so tests set them directly.
    """
    if builder._agent_id and builder._agent_name is None:
        builder._agent_name = "Agent"
    if not builder._conversation_id:
        builder._conversation_id = "conv-1"
    return builder


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestConversationBuilderCreate:
    def test_create_sets_aud_claim(self):
        builder = ConversationBuilder.create("my-app-id", "msteams")
        assert builder._claims["aud"] == "my-app-id"

    def test_create_sets_channel_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        assert builder._channel_id == "msteams"

    def test_create_teams_prefixes_agent_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        assert builder._agent_id == "28:app-id"

    def test_create_non_teams_no_prefix(self):
        builder = ConversationBuilder.create("app-id", "directline")
        assert builder._agent_id == "app-id"

    def test_create_with_requestor_id_sets_appid_claim(self):
        builder = ConversationBuilder.create(
            "app-id", "msteams", requestor_id="requestor-id"
        )
        assert builder._claims["appid"] == "requestor-id"

    def test_create_without_requestor_id_no_appid_claim(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        assert "appid" not in builder._claims

    def test_create_custom_service_url(self):
        builder = ConversationBuilder.create(
            "app-id", "msteams", service_url="https://custom.service/"
        )
        assert builder._service_url == "https://custom.service/"

    def test_create_default_service_url_teams(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        assert builder._service_url == "https://smba.trafficmanager.net/teams/"

    def test_create_default_service_url_generic(self):
        builder = ConversationBuilder.create("app-id", "directline")
        assert builder._service_url == "https://directline.botframework.com/"

    def test_create_returns_builder_instance(self):
        result = ConversationBuilder.create("app-id", "msteams")
        assert isinstance(result, ConversationBuilder)


# ---------------------------------------------------------------------------
# create_from_identity()
# ---------------------------------------------------------------------------


class TestConversationBuilderCreateFromIdentity:
    def test_create_from_identity_sets_channel_id(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)
        builder = ConversationBuilder.create_from_identity(identity, "msteams")
        assert builder._channel_id == "msteams"

    def test_create_from_identity_filters_claims(self):
        identity = ClaimsIdentity(
            claims={"aud": "app-id", "tid": "tenant", "unrelated": "drop"},
            is_authenticated=True,
        )
        builder = ConversationBuilder.create_from_identity(identity, "msteams")
        assert builder._claims["aud"] == "app-id"
        assert builder._claims["tid"] == "tenant"
        assert "unrelated" not in builder._claims

    def test_create_from_identity_teams_prefixes_agent(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)
        builder = ConversationBuilder.create_from_identity(identity, "msteams")
        assert builder._agent_id == "28:app-id"

    def test_create_from_identity_non_teams_no_prefix(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)
        builder = ConversationBuilder.create_from_identity(identity, "directline")
        assert builder._agent_id == "app-id"

    def test_create_from_identity_no_app_id_no_agent(self):
        identity = ClaimsIdentity(claims={}, is_authenticated=True)
        builder = ConversationBuilder.create_from_identity(identity, "msteams")
        assert builder._agent_id is None

    def test_create_from_identity_custom_service_url(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)
        builder = ConversationBuilder.create_from_identity(
            identity, "msteams", service_url="https://override/"
        )
        assert builder._service_url == "https://override/"

    def test_create_from_identity_returns_builder_instance(self):
        identity = ClaimsIdentity(claims={"aud": "app-id"}, is_authenticated=True)
        result = ConversationBuilder.create_from_identity(identity, "msteams")
        assert isinstance(result, ConversationBuilder)


# ---------------------------------------------------------------------------
# Fluent setters
# ---------------------------------------------------------------------------


class TestConversationBuilderSetters:
    def test_with_user_sets_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_user("user-id")
        assert builder._user_id == "user-id"

    def test_with_user_sets_name(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_user("user-id", "Alice")
        assert builder._user_name == "Alice"

    def test_with_user_returns_self(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        result = builder.with_user("user-id")
        assert result is builder

    def test_with_user_name_optional(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_user("user-id")
        assert builder._user_name is None

    def test_with_conversation_sets_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_conversation("conv-123")
        assert builder._conversation_id == "conv-123"

    def test_with_conversation_sets_tenant_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_conversation("conv-123", tenant_id="tenant-abc")
        assert builder._tenant_id == "tenant-abc"

    def test_with_conversation_sets_name(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_conversation("conv-123", conversation_name="My Chat")
        assert builder._conversation_name == "My Chat"

    def test_with_conversation_returns_self(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        result = builder.with_conversation("conv-123")
        assert result is builder

    def test_with_activity_id_sets_id(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        builder.with_activity_id("act-456")
        assert builder._activity_id == "act-456"

    def test_with_activity_id_returns_self(self):
        builder = ConversationBuilder.create("app-id", "msteams")
        result = builder.with_activity_id("act-456")
        assert result is builder


# ---------------------------------------------------------------------------
# build()
# ---------------------------------------------------------------------------


class TestConversationBuilderBuild:
    def test_build_sets_channel_id_on_reference(self):
        conv = _prep_build(ConversationBuilder.create("app-id", "msteams")).build()
        assert conv.conversation_reference.channel_id == "msteams"

    def test_build_sets_aud_claim(self):
        conv = _prep_build(ConversationBuilder.create("app-id", "msteams")).build()
        assert conv.claims.get("aud") == "app-id"

    def test_build_sets_service_url(self):
        conv = _prep_build(ConversationBuilder.create("app-id", "msteams")).build()
        assert (
            conv.conversation_reference.service_url
            == "https://smba.trafficmanager.net/teams/"
        )

    def test_build_sets_agent_with_teams_prefix(self):
        conv = _prep_build(ConversationBuilder.create("app-id", "msteams")).build()
        assert conv.conversation_reference.agent.id == "28:app-id"

    def test_build_no_agent_when_id_none(self):
        # When _agent_id is not set, build() passes bot=None to ConversationReference.
        # ConversationReference.agent has Field(None, alias="bot") with ChannelAccount type,
        # so explicitly passing bot=None raises a Pydantic ValidationError.
        from pydantic import ValidationError

        builder = ConversationBuilder()
        builder._channel_id = "directline"
        builder._service_url = "https://directline.botframework.com/"
        builder._conversation_id = "conv-placeholder"
        with pytest.raises(ValidationError):
            builder.build()

    def test_build_sets_user(self):
        conv = (
            _prep_build(ConversationBuilder.create("app-id", "msteams"))
            .with_user("user-oid", "Alice")
            .build()
        )
        assert conv.conversation_reference.user.id == "user-oid"
        assert conv.conversation_reference.user.name == "Alice"

    def test_build_sets_conversation_id(self):
        conv = (
            _prep_build(ConversationBuilder.create("app-id", "msteams"))
            .with_conversation("19:thread@thread.v2")
            .build()
        )
        assert conv.conversation_reference.conversation.id == "19:thread@thread.v2"

    def test_build_sets_conversation_tenant_id(self):
        conv = (
            _prep_build(ConversationBuilder.create("app-id", "msteams"))
            .with_conversation("conv-1", tenant_id="tenant-xyz")
            .build()
        )
        assert conv.conversation_reference.conversation.tenant_id == "tenant-xyz"

    def test_build_sets_activity_id(self):
        conv = (
            _prep_build(ConversationBuilder.create("app-id", "msteams"))
            .with_activity_id("act-1")
            .build()
        )
        assert conv.conversation_reference.activity_id == "act-1"

    def test_build_requires_channel_id(self):
        builder = ConversationBuilder()
        with pytest.raises(ValueError):
            builder.build()

    def test_build_with_identity_preserves_claims(self):
        identity = ClaimsIdentity(
            claims={"aud": "app-id", "tid": "tenant", "ver": "2.0"},
            is_authenticated=True,
        )
        conv = _prep_build(
            ConversationBuilder.create_from_identity(identity, "msteams")
        ).build()
        assert conv.claims["aud"] == "app-id"
        assert conv.claims["tid"] == "tenant"
        assert conv.claims["ver"] == "2.0"

    def test_build_conversation_is_conversation_instance(self):
        conv = _prep_build(ConversationBuilder.create("app-id", "msteams")).build()
        assert isinstance(conv, Conversation)

    def test_fluent_chaining_full_build(self):
        conv = (
            _prep_build(
                ConversationBuilder.create("app-id", "msteams", requestor_id="req-id")
            )
            .with_user("user-oid", "Bob")
            .with_conversation("19:thread@thread.v2", tenant_id="tenant-1")
            .with_activity_id("act-xyz")
            .build()
        )
        ref = conv.conversation_reference
        assert conv.claims["aud"] == "app-id"
        assert conv.claims["appid"] == "req-id"
        assert ref.user.id == "user-oid"
        assert ref.conversation.id == "19:thread@thread.v2"
        assert ref.activity_id == "act-xyz"
        assert ref.agent.id == "28:app-id"
