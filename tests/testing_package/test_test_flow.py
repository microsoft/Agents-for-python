# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio

import pytest

from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, RoleTypes
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.testing import TestAdapter, TestFlow


@pytest.mark.asyncio
async def test_send_assert_reply_and_assert_no_more_replies():
    adapter = TestAdapter()

    async def callback(context: TurnContext):
        await context.send_activity(f"Echo: {context.activity.text}")

    await (
        TestFlow(adapter, callback)
        .send("hello")
        .assert_reply("Echo: hello")
        .assert_no_more_replies(timeout=0.01)
        .start_test()
    )


@pytest.mark.asyncio
async def test_assert_reply_consumes_replies_in_order():
    adapter = TestAdapter()

    async def callback(context: TurnContext):
        await context.send_activity("first")
        await context.send_activity("second")

    await (
        TestFlow(adapter, callback)
        .send("go")
        .assert_reply("first")
        .assert_reply("second")
        .assert_no_more_replies(timeout=0.01)
        .start_test()
    )


@pytest.mark.asyncio
async def test_assert_no_more_replies_fails_when_reply_is_queued():
    adapter = TestAdapter()

    async def callback(context: TurnContext):
        await context.send_activity("extra")

    flow = TestFlow(adapter, callback).send("go").assert_no_more_replies(timeout=0.01)

    with pytest.raises(AssertionError, match="Expected no more replies"):
        await flow.start_test()


@pytest.mark.asyncio
async def test_chained_steps_start_as_tasks_but_wait_for_previous_steps():
    adapter = TestAdapter()
    events: list[str] = []
    first_started = asyncio.Event()
    release_first = asyncio.Event()

    async def callback(context: TurnContext):
        events.append(f"callback:{context.activity.text}")
        if context.activity.text == "one":
            first_started.set()
            await release_first.wait()
        await context.send_activity(f"reply:{context.activity.text}")

    flow = (
        TestFlow(adapter, callback)
        .send("one")
        .assert_reply("reply:one")
        .send("two")
        .assert_reply("reply:two")
    )

    await first_started.wait()
    await asyncio.sleep(0)
    assert events == ["callback:one"]

    release_first.set()
    await flow.start_test()
    assert events == ["callback:one", "callback:two"]


@pytest.mark.asyncio
async def test_send_conversation_update_uses_default_member():
    adapter = TestAdapter()

    async def callback(context: TurnContext):
        assert context.activity.type == ActivityTypes.conversation_update
        assert context.activity.members_added == [adapter.conversation.user]
        await context.send_activity("welcome")

    await (
        TestFlow(adapter, callback)
        .send_conversation_update()
        .assert_reply("welcome")
        .start_test()
    )


@pytest.mark.asyncio
async def test_test_activities_treats_agent_activities_as_expected_replies():
    adapter = TestAdapter()

    async def callback(context: TurnContext):
        await context.send_activity(f"Echo: {context.activity.text}")

    transcript = [
        Activity(
            type=ActivityTypes.message,
            text="hello",
            from_property=ChannelAccount(id="user", role=RoleTypes.user),
        ),
        Activity(
            type=ActivityTypes.message,
            text="Echo: hello",
            from_property=ChannelAccount(id="bot", role=RoleTypes.agent),
        ),
    ]

    await TestFlow(adapter, callback).test_activities(transcript).start_test()


@pytest.mark.asyncio
async def test_get_next_reply_async_returns_queued_reply_or_waits_for_next_reply():
    adapter = TestAdapter()
    context = adapter.create_turn_context(adapter.create_activity("inbound"))

    queued = Activity(type=ActivityTypes.message, text="already queued")
    await adapter.send_activities(context, [queued])

    assert await adapter.get_next_reply_async() is queued

    waiter = asyncio.create_task(adapter.get_next_reply_async())
    await asyncio.sleep(0)
    assert not waiter.done()

    next_reply = Activity(type=ActivityTypes.message, text="future reply")
    await adapter.send_activities(context, [next_reply])

    assert await asyncio.wait_for(waiter, timeout=0.1) is next_reply
