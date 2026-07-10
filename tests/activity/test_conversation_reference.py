from uuid import UUID

import pytest
from pydantic import ValidationError

from microsoft_agents.activity import (
    ActivityEventNames,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ConversationReference,
)


def _create_conversation_reference(user: ChannelAccount | None = None):
    return ConversationReference(
        activity_id="activity-123",
        channel_id="msteams",
        service_url="https://smba.trafficmanager.net/teams/",
        conversation=ConversationAccount(id="conversation-123", name="Test Chat"),
        user=user if user is not None else ChannelAccount(id="user-123", name="User"),
        agent=ChannelAccount(id="agent-123", name="Agent"),
        locale="en-US",
    )


def test_get_continuation_activity_sets_expected_fields():
    conversation_reference = _create_conversation_reference()

    continuation_activity = conversation_reference.get_continuation_activity()

    UUID(continuation_activity.id)
    assert continuation_activity.id != conversation_reference.activity_id
    assert continuation_activity.type == ActivityTypes.event
    assert continuation_activity.name == ActivityEventNames.continue_conversation
    assert continuation_activity.channel_id == conversation_reference.channel_id
    assert continuation_activity.service_url == conversation_reference.service_url
    assert continuation_activity.conversation == conversation_reference.conversation
    assert continuation_activity.recipient == conversation_reference.agent
    assert continuation_activity.from_property == conversation_reference.user
    assert continuation_activity.relates_to == conversation_reference


def test_get_continuation_activity_generates_new_id_each_time():
    conversation_reference = _create_conversation_reference()

    first_activity = conversation_reference.get_continuation_activity()
    second_activity = conversation_reference.get_continuation_activity()

    assert first_activity.id != second_activity.id


def test_get_continuation_activity_raises_when_user_is_missing():
    conversation_reference = _create_conversation_reference(user=None)
    conversation_reference.user = None

    with pytest.raises(ValidationError):
        conversation_reference.get_continuation_activity()
