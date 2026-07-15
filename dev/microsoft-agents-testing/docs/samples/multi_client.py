#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Multi-Client & Advanced Patterns — multiple users, child clients, templates.

Features demonstrated:
  - scenario.run() + ClientFactory — create multiple independent clients.
  - ClientConfig                   — per-client auth tokens, headers, templates.
  - ActivityTemplate               — set default fields on every outgoing activity.
  - AgentClient.child()            — scoped transcript isolation.
  - Transcript hierarchy           — parent/child exchange propagation.

Run::

    python -m docs.samples.multi_client
"""

import asyncio

from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    ClientConfig,
    ActivityTemplate,
    Transcript,
    ConversationTranscriptFormatter,
    DetailLevel,
)


# ---------------------------------------------------------------------------
# Agent — identifies who is talking
# ---------------------------------------------------------------------------

async def init_agent(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState):
        sender = ctx.activity.from_property
        name = sender.name if sender and sender.name else "Unknown"
        await ctx.send_activity(f"Hello {name}, you said: {ctx.activity.text}")


scenario = AiohttpScenario(init_agent, use_jwt_middleware=False)


# ---------------------------------------------------------------------------
# 1) Multiple clients via ClientFactory
# ---------------------------------------------------------------------------

async def demo_multi_client() -> None:
    """Create two clients with different identities in the same scenario run."""
    print("── 1. Multiple clients via scenario.run() ──\n")

    async with scenario.run() as factory:
        # Each factory() call creates an independent client.
        # Use ClientConfig + ActivityTemplate to give each a different identity.

        alice = await factory(
            ClientConfig(
                activity_template=ActivityTemplate({
                    "from.id": "alice",
                    "from.name": "Alice",
                })
            )
        )

        bob = await factory(
            ClientConfig(
                activity_template=ActivityTemplate({
                    "from.id": "bob",
                    "from.name": "Bob",
                })
            )
        )

        await alice.send_expect_replies("Hi from Alice")
        await bob.send_expect_replies("Hi from Bob")

        # Both share the scenario-level transcript
        alice.expect(history=True).that_for_any(text="~Alice")
        bob.expect(history=True).that_for_any(text="~Bob")

        print("Alice's last reply:", (await alice.send_expect_replies("ping"))[0].text)
        print("Bob's last reply:  ", (await bob.send_expect_replies("pong"))[0].text)

    print()


# ---------------------------------------------------------------------------
# 2) ActivityTemplate — set defaults for all outgoing activities
# ---------------------------------------------------------------------------

async def demo_activity_template() -> None:
    """Show how templates apply default fields automatically."""
    print("── 2. ActivityTemplate defaults ──\n")

    config = ClientConfig(
        activity_template=ActivityTemplate(
            channel_id="demo-channel",
            locale="en-US",
            **{
                "from.id": "demo-user",
                "from.name": "Demo User",
                "conversation.id": "demo-conv-001",
            },
        )
    )

    async with scenario.client(config) as client:
        replies = await client.send_expect_replies("template test")
        print(f"Agent replied: {replies[0].text}")

        # The template enriched the outgoing activity with defaults —
        # we can verify via the transcript's recorded request.
        exchange = client.ex_history()[0]
        req = exchange.request
        print(f"  channel_id  : {req.channel_id}")
        print(f"  locale      : {req.locale}")
        print(f"  from.id     : {req.from_property.id}")
        print(f"  from.name   : {req.from_property.name}")
        print(f"  conversation: {req.conversation.id}")

    print()


# ---------------------------------------------------------------------------
# 3) Child clients — transcript scoping
# ---------------------------------------------------------------------------

async def demo_child_client() -> None:
    """AgentClient.child() creates a scoped transcript branch."""
    print("── 3. Child clients & transcript hierarchy ──\n")

    async with scenario.client() as parent:
        await parent.send_expect_replies("Parent message 1")

        child = parent.child()
        await child.send_expect_replies("Child message 1")
        await child.send_expect_replies("Child message 2")

        await parent.send_expect_replies("Parent message 2")

        # Parent transcript sees everything (its own + propagated from child)
        print(f"Parent transcript exchanges: {len(parent.transcript)}")

        # Child transcript sees only its own exchanges
        print(f"Child transcript exchanges : {len(child.transcript)}")

        print("\n--- Parent view ---")
        ConversationTranscriptFormatter(
            user_label="User", agent_label="Agent", detail=DetailLevel.STANDARD
        ).print(parent.transcript)

        print("\n--- Child view ---")
        ConversationTranscriptFormatter(
            user_label="User", agent_label="Agent", detail=DetailLevel.STANDARD
        ).print(child.transcript)

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("Multi-Client & Advanced Patterns\n")

    await demo_multi_client()
    await demo_activity_template()
    await demo_child_client()

    print("All multi-client demos complete.")


if __name__ == "__main__":
    asyncio.run(main())
