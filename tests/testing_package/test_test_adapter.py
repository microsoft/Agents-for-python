# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio
from collections.abc import Awaitable, Callable

import pytest

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    Channels,
    ConversationReference,
    RoleTypes,
)
from microsoft_agents.hosting.core import (
    ClaimsIdentity,
    TurnContext,
    UserTokenClientBase,
)
from microsoft_agents.testing import TestAdapter
from microsoft_agents.testing import MockUserTokenClient


@pytest.mark.asyncio
async def test_process_activity_provides_a_channel_shaped_turn_to_agent_code():
    adapter = TestAdapter(channel_id=Channels.ms_teams)
    identity = ClaimsIdentity({"sub": "test-user"}, True)
    received_context: TurnContext | None = None

    async def callback(context: TurnContext):
        nonlocal received_context
        received_context = context
        await context.send_activity(f"received:{context.activity.text}")

    incoming = Activity(type=ActivityTypes.message, text="hello")
    result = await adapter.process_activity(identity, incoming, callback)

    assert result is None
    assert received_context is not None
    assert received_context.identity is identity
    assert received_context.activity is incoming
    assert incoming.type == ActivityTypes.message
    assert incoming.channel_id == Channels.ms_teams
    assert incoming.from_property == adapter.conversation.user
    assert incoming.recipient == adapter.conversation.agent
    assert incoming.conversation == adapter.conversation.conversation
    assert incoming.service_url == adapter.conversation.service_url
    assert incoming.id
    assert incoming.timestamp is not None
    assert incoming.local_timestamp is not None
    assert adapter.get_next_reply().text == "received:hello"


@pytest.mark.asyncio
async def test_process_activity_preserves_an_explicit_user_sender():
    adapter = TestAdapter()
    sender = ChannelAccount(id="another-user", role=RoleTypes.user)
    incoming = Activity(
        type=ActivityTypes.event,
        channel_id=Channels.webchat,
        from_property=sender,
    )

    async def callback(context: TurnContext):
        assert context.activity.from_property is sender
        assert context.activity.type == ActivityTypes.event
        assert context.activity.channel_id == Channels.webchat

    await adapter.process_activity(adapter.claims_identity, incoming, callback)


@pytest.mark.asyncio
async def test_process_activity_replaces_an_agent_sender_with_the_test_user():
    adapter = TestAdapter()
    incoming = Activity(
        type=ActivityTypes.message,
        from_property=ChannelAccount(id="bot-from-transcript", role=RoleTypes.agent),
    )

    async def callback(context: TurnContext):
        assert context.activity.from_property == adapter.conversation.user

    await adapter.process_activity(adapter.claims_identity, incoming, callback)


@pytest.mark.asyncio
async def test_turn_context_exposes_the_configured_user_token_client():
    token_client = MockUserTokenClient()
    adapter = TestAdapter(user_token_client=token_client)

    async def callback(context: TurnContext):
        assert context.services.get(UserTokenClientBase) is token_client

    await adapter.send_text_to_bot("authenticate", callback)


@pytest.mark.asyncio
async def test_middleware_can_transform_a_turn_before_the_agent_handles_it():
    adapter = TestAdapter()
    events: list[str] = []

    class PrefixMiddleware:
        async def on_turn(
            self,
            context: TurnContext,
            logic: Callable[[TurnContext], Awaitable[None]],
        ):
            events.append("middleware")
            context.activity.text = f"changed:{context.activity.text}"
            await logic(context)

    adapter.use(PrefixMiddleware())

    async def callback(context: TurnContext):
        events.append(f"agent:{context.activity.text}")

    await adapter.send_text_to_bot("original", callback)

    assert events == ["middleware", "agent:changed:original"]


@pytest.mark.asyncio
async def test_send_activities_returns_ids_and_captures_replies_in_send_order():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))
    replies = [
        Activity(type=ActivityTypes.typing),
        Activity(type=ActivityTypes.message, text="done", id="provided-id"),
    ]

    responses = await adapter.send_activities(context, replies)

    assert [response.id for response in responses] == [
        replies[0].id,
        "provided-id",
    ]
    assert all(reply.timestamp is not None for reply in replies)
    assert adapter.get_activity_snapshot() == replies
    assert adapter.get_next_reply() is replies[0]
    assert adapter.get_next_reply() is replies[1]
    assert adapter.get_next_reply() is None


@pytest.mark.asyncio
async def test_waiting_consumers_receive_replies_in_arrival_order():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))
    first_waiter = asyncio.create_task(adapter.get_next_reply_async())
    second_waiter = asyncio.create_task(adapter.get_next_reply_async())
    await asyncio.sleep(0)

    first_reply = Activity(type=ActivityTypes.message, text="first")
    second_reply = Activity(type=ActivityTypes.message, text="second")
    await adapter.send_activities(context, [first_reply, second_reply])

    assert await first_waiter is first_reply
    assert await second_waiter is second_reply
    assert adapter.get_activity_snapshot() == []


@pytest.mark.asyncio
async def test_a_cancelled_consumer_does_not_drop_the_next_reply():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))
    cancelled_waiter = asyncio.create_task(adapter.get_next_reply_async())
    await asyncio.sleep(0)
    cancelled_waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await cancelled_waiter

    reply = Activity(type=ActivityTypes.message, text="still delivered")
    await adapter.send_activities(context, [reply])

    assert adapter.get_next_reply() is reply


@pytest.mark.asyncio
async def test_update_and_delete_change_only_the_targeted_queued_reply():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))
    first = Activity(type=ActivityTypes.message, text="first", id="first")
    second = Activity(type=ActivityTypes.message, text="second", id="second")
    third = Activity(type=ActivityTypes.message, text="third", id="third")
    await adapter.send_activities(context, [first, second, third])

    replacement = Activity(
        type=ActivityTypes.message, text="second revised", id="second"
    )
    update_response = await adapter.update_activity(context, replacement)
    await adapter.delete_activity(
        context,
        ConversationReference(
            conversation=adapter.conversation.conversation,
            activity_id="first",
        ),
    )

    assert update_response.id == "second"
    assert adapter.get_activity_snapshot() == [replacement, third]


@pytest.mark.asyncio
async def test_update_and_delete_unknown_replies_leave_the_queue_unchanged():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))
    reply = Activity(type=ActivityTypes.message, text="reply", id="known")
    await adapter.send_activities(context, [reply])

    response = await adapter.update_activity(
        context, Activity(type=ActivityTypes.message, id="unknown")
    )
    await adapter.delete_activity(
        context,
        ConversationReference(
            conversation=adapter.conversation.conversation,
            activity_id="unknown",
        ),
    )

    assert response.id is None
    assert adapter.get_activity_snapshot() == [reply]


@pytest.mark.asyncio
async def test_proactive_turn_uses_the_supplied_activity_and_identity():
    adapter = TestAdapter()
    identity = ClaimsIdentity({"sub": "proactive-user"}, True)
    continuation = adapter.create_activity("")
    continuation.type = ActivityTypes.event
    continuation.name = "continue"

    async def callback(context: TurnContext):
        assert context.activity is continuation
        assert context.identity is identity
        await context.send_activity("proactive reply")

    await adapter.process_proactive(
        identity, continuation, "ignored-audience", callback
    )

    assert adapter.get_next_reply().text == "proactive reply"


def test_create_conversation_model_and_create_activity_honor_public_configuration():
    conversation = TestAdapter.create_conversation_model(
        channel_id=Channels.webchat,
        conv_id="conversation-42",
        conv_name="Support",
        user_id="customer-7",
        user_name="Customer",
        bot_id="assistant-3",
        bot_name="Assistant",
        locale="fr-FR",
    )
    adapter = TestAdapter(conversation=conversation)
    adapter.locale = "de-DE"

    activity = adapter.create_activity("Guten Tag")

    assert conversation.channel_id == Channels.webchat
    assert conversation.conversation.id == "conversation-42"
    assert conversation.user.id == "customer-7"
    assert conversation.agent.id == "assistant-3"
    assert activity.text == "Guten Tag"
    assert activity.locale == "de-DE"
    assert activity.from_property == conversation.user
    assert activity.recipient == conversation.agent
    assert activity.conversation == conversation.conversation


@pytest.mark.asyncio
async def test_adapter_rejects_unsupported_operations_and_invalid_sends():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))

    with pytest.raises(ValueError, match="cannot be empty"):
        await adapter.send_activities(context, [])

    with pytest.raises(NotImplementedError):
        await adapter.create_conversation(
            "app",
            Channels.test,
            "https://example.test",
            "audience",
            None,
            None,
        )


def test_token_setup_helpers_reject_a_non_mock_token_client():
    adapter = TestAdapter(user_token_client=object())

    with pytest.raises(TypeError, match="not a MockUserTokenClient"):
        adapter.add_user_token("connection", "test", "user", "token")

    with pytest.raises(TypeError, match="not a MockUserTokenClient"):
        adapter.add_exchangeable_token(
            "connection", "test", "user", "exchange", "token"
        )

    with pytest.raises(TypeError, match="not a MockUserTokenClient"):
        adapter.raise_on_exchange_request("connection", "test", "user", "exchange")
