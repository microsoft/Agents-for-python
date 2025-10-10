import pytest

from microsoft_agents.activity import (
    ChannelId,
    ConversationReference,
    ConversationAccount,
)

DATA = [
    [
        ConversationReference(
            channel_id="parent:sub_channel",
            conversation=ConversationAccount(id="conv1"),
        ),
        {
            "channel_id": "parent:sub_channel",
            "conversation": {"id": "conv1"},
        },
    ],
    [
        ConversationReference(
            channel_id=ChannelId(channel="parent", sub_channel="sub_channel"),
            conversation=ConversationAccount(id="conv1"),
        ),
        {
            "channel_id": "parent:sub_channel",
            "conversation": {"id": "conv1"},
        },
    ],
    [
        ConversationReference(conversation=ConversationAccount(id="conv1")),
        {
            "conversation": {"id": "conv1"},
        },
    ],
]

DATA_WITH_ALIAS = [
    [
        ConversationReference(
            channel_id="parent:sub_channel",
            conversation=ConversationAccount(id="conv1"),
        ),
        {
            "channelId": "parent:sub_channel",
            "conversation": {"id": "conv1"},
        },
    ],
    [
        ConversationReference(
            channel_id=ChannelId(channel="parent", sub_channel="sub_channel"),
            conversation=ConversationAccount(id="conv1"),
        ),
        {
            "channelId": "parent:sub_channel",
            "conversation": {"id": "conv1"},
        },
    ],
    [
        ConversationReference(conversation=ConversationAccount(id="conv1")),
        {
            "conversation": {"id": "conv1"},
        },
    ],
]

VALIDATION_ERR_DATA_FROM_JSON = [
    {
        "channel_id": "parent:sub_channel",
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {},
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {"id": ""},
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {"id": None},
    },
    {
        "channel_id": {"sub_channel": "sub_channel"},
        "conversation": {"id": "conv1"},
    },
    {
        "channelId": "parent:sub_channel",
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {},
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {"id": ""},
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {"id": None},
    },
    {
        "channelId": {"sub_channel": "sub_channel"},
        "conversation": {"id": "conv1"},
    },
]

VALIDATION_ERR_DATA_FROM_KWARGS = [
    {
        "channel_id": "parent:sub_channel",
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {},
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {"id": ""},
    },
    {
        "channel_id": "parent:sub_channel",
        "conversation": {"id": None},
    },
    {
        "channel_id": None,
        "conversation": {"id": "conv1"},
    },
    {
        "channel_id": "",
        "conversation": {"id": "conv1"},
    },
    {
        "channel_id": {"sub_channel": "sub_channel"},
        "conversation": {"id": "conv1"},
    },
    {
        "channelId": "parent:sub_channel",
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {},
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {"id": ""},
    },
    {
        "channelId": "parent:sub_channel",
        "conversation": {"id": None},
    },
    {
        "channelId": None,
        "conversation": {"id": "conv1"},
    },
    {
        "channelId": "",
        "conversation": {"id": "conv1"},
    },
    {
        "channelId": {"sub_channel": "sub_channel"},
        "conversation": {"id": "conv1"},
    },
]


@pytest.mark.parametrize("instance, expected", DATA)
def test_conversation_reference_io(instance, expected):
    if "channel_id" in expected:
        assert instance.model_dump(exclude_unset=True) == expected
    else:
        assert instance.model_dump(exclude_unset=True, by_alias=True) == expected
    assert ConversationReference.model_validate(expected) == instance


@pytest.mark.parametrize("data", VALIDATION_ERR_DATA_FROM_JSON)
def test_conversation_reference_validation_error(data):
    with pytest.raises(Exception):
        ConversationReference.model_validate(data)


@pytest.mark.parametrize("data", VALIDATION_ERR_DATA_FROM_KWARGS)
def test_conversation_reference_validation_error_kwargs(data):
    with pytest.raises(Exception):
        ConversationReference.model_validate(**data)
