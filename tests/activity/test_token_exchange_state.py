import base64
import json

import pytest

from microsoft_agents.activity import (
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
    TokenExchangeState,
)


def _create_conversation_reference(
    activity_id: str = "activity-123",
    conversation_id: str = "conversation-123",
) -> ConversationReference:
    return ConversationReference(
        activity_id=activity_id,
        channel_id="msteams",
        service_url="https://smba.trafficmanager.net/teams/",
        conversation=ConversationAccount(id=conversation_id),
        user=ChannelAccount(id="user-123", name="User"),
        agent=ChannelAccount(id="agent-123", name="Agent"),
    )


def _decode_state(encoded_state: str) -> dict:
    return json.loads(base64.b64decode(encoded_state).decode("utf-8"))


def test_get_encoded_state_returns_base64_encoded_json_with_aliases():
    token_exchange_state = TokenExchangeState(
        connection_name="connection-name",
        conversation=_create_conversation_reference(),
        agent_url="https://agent.example.com/api/messages",
        ms_app_id="app-id",
    )

    decoded_state = _decode_state(token_exchange_state.get_encoded_state())

    assert decoded_state["connectionName"] == "connection-name"
    assert decoded_state["bot_url"] == "https://agent.example.com/api/messages"
    assert decoded_state["msAppId"] == "app-id"
    assert decoded_state["conversation"]["activityId"] == "activity-123"
    assert decoded_state["conversation"]["channelId"] == "msteams"
    assert (
        decoded_state["conversation"]["serviceUrl"]
        == "https://smba.trafficmanager.net/teams/"
    )
    assert decoded_state["conversation"]["conversation"]["id"] == "conversation-123"
    assert decoded_state["conversation"]["user"]["id"] == "user-123"
    assert decoded_state["conversation"]["bot"]["id"] == "agent-123"
    assert "relatesTo" not in decoded_state
    assert "agentUrl" not in decoded_state


def test_get_encoded_state_includes_related_conversation_when_set():
    token_exchange_state = TokenExchangeState(
        connection_name="connection-name",
        conversation=_create_conversation_reference(),
        relates_to=_create_conversation_reference(
            activity_id="parent-activity", conversation_id="parent-conversation"
        ),
        agent_url="https://agent.example.com/api/messages",
        ms_app_id="app-id",
    )

    decoded_state = _decode_state(token_exchange_state.get_encoded_state())

    assert decoded_state["relatesTo"]["activityId"] == "parent-activity"
    assert decoded_state["relatesTo"]["conversation"]["id"] == "parent-conversation"


def test_token_exchange_state_accepts_bot_url_alias():
    token_exchange_state = TokenExchangeState(
        connection_name="connection-name",
        conversation=_create_conversation_reference(),
        bot_url="https://agent.example.com/api/messages",
        ms_app_id="app-id",
    )

    decoded_state = _decode_state(token_exchange_state.get_encoded_state())

    assert token_exchange_state.agent_url == "https://agent.example.com/api/messages"
    assert decoded_state["bot_url"] == "https://agent.example.com/api/messages"
