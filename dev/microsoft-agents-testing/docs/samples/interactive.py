#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Interactive REPL — chat with an in-process echo agent.

Features demonstrated:
  - AiohttpScenario  — host an agent in-process, no external server needed.
  - AgentClient      — send messages & receive replies.
  - Transcript       — automatic exchange recording.
  - ConversationTranscriptFormatter — pretty-print the session on exit.

Run::

    python -m docs.samples.interactive
"""

import asyncio

from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    ConversationTranscriptFormatter,
    DetailLevel,
)


# ---------------------------------------------------------------------------
# 1) Define the agent — a simple echo handler
# ---------------------------------------------------------------------------

async def init_echo_agent(env: AgentEnvironment) -> None:
    """Register a message handler that echoes user input."""

    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState) -> None:
        await context.send_activity(f"You said: {context.activity.text}")


# ---------------------------------------------------------------------------
# 2) Create the scenario
# ---------------------------------------------------------------------------

scenario = AiohttpScenario(init_echo_agent, use_jwt_middleware=False)


# ---------------------------------------------------------------------------
# 3) Run a REPL loop
# ---------------------------------------------------------------------------

async def main() -> None:
    async with scenario.client() as client:
        print("Agent is running.  Type a message (or 'quit' to exit).\n")

        while True:
            user_input = input("You: ")
            if user_input.strip().lower() in ("quit", "exit", "q"):
                break

            replies = await client.send_expect_replies(user_input)
            for reply in replies:
                print(f"Agent: {reply.text}")
            print()

        # Print the full conversation transcript on exit
        print("\n--- Session transcript ---")
        ConversationTranscriptFormatter(detail=DetailLevel.DETAILED).print(
            client.transcript
        )


if __name__ == "__main__":
    asyncio.run(main())
