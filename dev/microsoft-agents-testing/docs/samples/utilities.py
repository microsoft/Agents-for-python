#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Utilities - contains, poll, send, and ex_send.

Features demonstrated:
  - contains - search nested model, dict, and iterable values.
  - poll     - wait for asynchronous side effects.
  - send     - quick activity send against a running agent URL.
  - ex_send  - send and inspect Exchange metadata.

Run::

    python -m docs.samples.utilities
"""

import asyncio

from microsoft_agents.activity import Activity, Attachment, DeliveryModes
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import AiohttpScenario, AgentEnvironment, ScenarioConfig
from microsoft_agents.testing.utils import contains, ex_send, poll, send

HERO_CARD = "application/vnd.microsoft.card.hero"
AGENT_URL = "http://127.0.0.1:3978/api/messages"


async def init_agent(env: AgentEnvironment) -> None:
    """Register an agent that replies with text and a nested attachment."""

    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState) -> None:
        await ctx.send_activity(
            Activity(
                type="message",
                text=f"Echo: {ctx.activity.text}",
                attachments=[
                    Attachment(
                        content_type=HERO_CARD,
                        content={"title": "Utility sample"},
                    )
                ],
            )
        )


scenario = AiohttpScenario(
    init_agent,
    config=ScenarioConfig(callback_server_port=9379),
    use_jwt_middleware=False,
)


async def demo_contains() -> None:
    """Use contains with Expect and Select."""
    print("-- contains --")

    async with scenario.client() as client:
        await client.send_expect_replies("show me a card")

        client.expect().that_for_any(attachments=contains(content_type=HERO_CARD))

        selected = client.select().where(contains(content_type=HERO_CARD)).get()
        print(f"Activities with hero cards: {len(selected)}")


async def demo_poll() -> None:
    """Wait for a side effect to appear."""
    print("-- poll --")

    state = {"saved": False}

    async def save_later() -> None:
        await asyncio.sleep(0.05)
        state["saved"] = True

    asyncio.create_task(save_later())
    await poll(lambda: state["saved"], timeout=1.0, interval=0.01)
    print("Asynchronous state was saved.")


async def demo_send_helpers() -> None:
    """Use send and ex_send against a running agent endpoint."""
    print("-- send / ex_send --")

    async with scenario.run():
        replies = await send("hello from send", AGENT_URL, listen_duration=0.2)
        print(f"send returned: {replies[0].text}")

        exchange_activity = Activity(
            type="message",
            text="hello from ex_send",
            delivery_mode=DeliveryModes.expect_replies,
        )

        exchanges = await ex_send(exchange_activity, AGENT_URL, listen_duration=0.0)
        print(f"ex_send request text: {exchanges[0].request.text}")
        print(f"ex_send response count: {len(exchanges[0].responses)}")


async def main() -> None:
    print("Utilities Demo\n")

    await demo_contains()
    await demo_poll()
    await demo_send_helpers()

    print("\nAll utility demos complete.")


if __name__ == "__main__":
    asyncio.run(main())
