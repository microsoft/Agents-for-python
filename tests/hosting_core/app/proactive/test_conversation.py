"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

import pytest
from unittest.mock import MagicMock

from microsoft_agents.activity import ConversationAccount, ConversationReference
from microsoft_agents.hosting.core.app.proactive import Conversation
from microsoft_agents.hosting.core.authorization import ClaimsIdentity
from microsoft_agents.hosting.core.channel_adapter import ChannelAdapter


def _make_reference(
    conversation_id="conv-1",
    service_url="https://smba.trafficmanager.net/teams/",
    channel_id="msteams",
):
    return ConversationReference(
        conversation=ConversationAccount(id=conversation_id),
        service_url=service_url,
        channel_id=channel_id,
    )


class TestConversationInit:
    def test_init_with_dict_keeps_allowed_claims(self):
        claims = {
            "aud": "app-id",
            "azp": "azp-val",
            "appid": "app-id",
            "idtyp": "app",
            "ver": "2.0",
            "iss": "issuer",
            "tid": "tenant-id",
        }
        conv = Conversation(claims=claims, conversation_reference=_make_reference())
        for key in ("aud", "azp", "appid", "idtyp", "ver", "iss", "tid"):
            assert conv.claims[key] == claims[key]

    def test_init_with_dict_filters_unknown_claims(self):
        claims = {"aud": "app-id", "extra": "should-be-filtered", "another": "drop"}
        conv = Conversation(claims=claims, conversation_reference=_make_reference())
        assert "extra" not in conv.claims
        assert "another" not in conv.claims
        assert conv.claims["aud"] == "app-id"

    def test_init_with_claims_identity_filters_correctly(self):
        identity = ClaimsIdentity(
            claims={"aud": "app-id", "tid": "tenant", "unrelated": "drop"},
            is_authenticated=True,
        )
        conv = Conversation(claims=identity, conversation_reference=_make_reference())
        assert conv.claims["aud"] == "app-id"
        assert conv.claims["tid"] == "tenant"
        assert "unrelated" not in conv.claims

    def test_init_stores_conversation_reference(self):
        ref = _make_reference()
        conv = Conversation(claims={}, conversation_reference=ref)
        assert conv.conversation_reference is ref

    def test_init_empty_claims_dict(self):
        conv = Conversation(claims={}, conversation_reference=_make_reference())
        assert conv.claims == {}


class TestConversationFromTurnContext:
    def test_from_turn_context_extracts_reference_and_identity(self):
        ref = _make_reference("ctx-conv")
        identity = ClaimsIdentity(
            claims={"aud": "app-id", "tid": "t"}, is_authenticated=True
        )

        ctx = MagicMock()
        ctx.activity.get_conversation_reference.return_value = ref
        ctx.turn_state = {ChannelAdapter.AGENT_IDENTITY_KEY: identity}

        conv = Conversation.from_turn_context(ctx)

        assert conv.conversation_reference is ref
        assert conv.claims.get("aud") == "app-id"
        assert conv.claims.get("tid") == "t"

    def test_from_turn_context_handles_missing_identity(self):
        ref = _make_reference("ctx-conv")
        ctx = MagicMock()
        ctx.activity.get_conversation_reference.return_value = ref
        ctx.turn_state = {}

        conv = Conversation.from_turn_context(ctx)

        assert conv.conversation_reference is ref
        assert conv.claims == {}


class TestConversationClaimsHelpers:
    def test_claims_from_identity_keeps_allowed_keys(self):
        identity = ClaimsIdentity(
            claims={"aud": "a", "tid": "t", "ver": "2.0", "other": "drop"},
            is_authenticated=True,
        )
        result = Conversation.claims_from_identity(identity)
        assert result == {"aud": "a", "tid": "t", "ver": "2.0"}

    def test_claims_from_identity_empty_claims(self):
        identity = ClaimsIdentity(claims={}, is_authenticated=True)
        result = Conversation.claims_from_identity(identity)
        assert result == {}

    def test_identity_from_claims_is_authenticated(self):
        claims = {"aud": "app-id", "tid": "tenant"}
        identity = Conversation.identity_from_claims(claims)
        assert identity.is_authenticated is True

    def test_identity_from_claims_preserves_values(self):
        claims = {"aud": "app-id", "tid": "tenant", "ver": "2.0"}
        identity = Conversation.identity_from_claims(claims)
        assert identity.claims["aud"] == "app-id"
        assert identity.claims["tid"] == "tenant"
        assert identity.claims["ver"] == "2.0"

    def test_identity_from_claims_does_not_mutate_input(self):
        claims = {"aud": "app-id"}
        Conversation.identity_from_claims(claims)
        assert claims == {"aud": "app-id"}


class TestConversationValidate:
    def test_validate_ok(self):
        conv = Conversation(claims={}, conversation_reference=_make_reference())
        conv.validate()  # must not raise

    def test_validate_missing_conversation_reference_raises(self):
        conv = Conversation(claims={}, conversation_reference=_make_reference())
        conv.conversation_reference = None
        with pytest.raises(ValueError, match="conversation_reference"):
            conv.validate()

    def test_validate_missing_conversation_account_raises(self):
        ref = _make_reference()
        conv = Conversation(claims={}, conversation_reference=ref)
        # ConversationReference.conversation is a required Pydantic field so it cannot
        # be omitted at construction time.  Set it to None after construction to exercise
        # the Conversation.validate() guard directly.
        conv.conversation_reference.conversation = None
        with pytest.raises(ValueError, match="conversation"):
            conv.validate()

    def test_validate_missing_service_url_raises(self):
        ref = ConversationReference(
            conversation=ConversationAccount(id="conv1"),
            channel_id="msteams",
        )
        conv = Conversation(claims={}, conversation_reference=ref)
        with pytest.raises(ValueError, match="service_url"):
            conv.validate()


class TestConversationSerialization:
    def test_store_item_to_json_contains_claims(self):
        conv = Conversation(
            claims={"aud": "app-id", "tid": "tenant"},
            conversation_reference=_make_reference(),
        )
        data = conv.store_item_to_json()
        assert data["claims"]["aud"] == "app-id"
        assert data["claims"]["tid"] == "tenant"

    def test_store_item_to_json_contains_conversation_reference(self):
        conv = Conversation(
            claims={"aud": "app-id"},
            conversation_reference=_make_reference("my-conv"),
        )
        data = conv.store_item_to_json()
        assert "conversation_reference" in data

    def test_round_trip_preserves_claims(self):
        original = Conversation(
            claims={"aud": "app-id", "tid": "tenant"},
            conversation_reference=_make_reference("rt-conv"),
        )
        json_data = original.store_item_to_json()
        restored = Conversation.from_json_to_store_item(json_data)
        assert restored.claims == {"aud": "app-id", "tid": "tenant"}

    def test_round_trip_preserves_conversation_id(self):
        original = Conversation(
            claims={},
            conversation_reference=_make_reference("rt-conv-id"),
        )
        json_data = original.store_item_to_json()
        restored = Conversation.from_json_to_store_item(json_data)
        assert restored.conversation_reference.conversation.id == "rt-conv-id"

    def test_round_trip_preserves_service_url(self):
        original = Conversation(
            claims={},
            conversation_reference=_make_reference(
                service_url="https://custom.service/"
            ),
        )
        json_data = original.store_item_to_json()
        restored = Conversation.from_json_to_store_item(json_data)
        assert restored.conversation_reference.service_url == "https://custom.service/"
