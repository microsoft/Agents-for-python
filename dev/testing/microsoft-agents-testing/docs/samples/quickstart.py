#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Quickstart — the simplest possible agent test, no pytest required.

Features demonstrated:
  - AiohttpScenario      — in-process agent hosting.
  - scenario.client()    — async context manager that starts the agent,
                            yields an AgentClient, and tears everything down.
  - send_expect_replies() — send a message and get the inline replies.

Run::

    python -m docs.samples.quickstart
"""

import asyncio

from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

async def init_echo(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState) -> None:
        await ctx.send_activity(f"Echo: {ctx.activity.text}")


scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

async def main() -> None:
    async with scenario.client() as client:
        # send_expect_replies sends with delivery_mode=expect_replies
        # and returns the agent's response activities directly.
        replies = await client.send_expect_replies("Hello, World!")

        for reply in replies:
            print(f"Agent replied: {reply.text}")
        # Expected output:
        #   Agent replied: Echo: Hello, World!


if __name__ == "__main__":
    asyncio.run(main())
