# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest

from microsoft_agents.testing import TestFlow


@pytest.mark.asyncio
async def test_echoes_a_user_message(flow: TestFlow) -> None:
    await flow.test("hello", "Echo: hello").start_test()


@pytest.mark.asyncio
async def test_help_explains_how_to_use_the_agent(flow: TestFlow) -> None:
    await flow.test(
        "/help",
        "Send any message to receive an echo response.",
    ).start_test()


@pytest.mark.asyncio
async def test_welcomes_new_conversation_members(flow: TestFlow) -> None:
    await (
        flow.send_conversation_update()
        .assert_reply("Welcome! Send a message and I will echo it back.")
        .start_test()
    )


@pytest.mark.asyncio
async def test_handles_a_multi_turn_conversation(flow: TestFlow) -> None:
    await (
        flow.test("first", "Echo: first")
        .test("second", "Echo: second")
        .assert_no_more_replies(timeout=0.01)
        .start_test()
    )
