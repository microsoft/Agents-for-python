#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript Formatting - visualize agent conversations for debugging.

Features demonstrated:
  - Transcript / Exchange - automatic recording of every request and response.
  - ConversationTranscriptFormatter - chat-style transcript view.
  - ActivityTranscriptFormatter     - flat JSON array of Activity objects.
  - JsonTranscriptFormatter         - JSON array of Exchange objects.
  - print_conversation / print_activities / print_json convenience functions.

Run::

    python -m docs.samples.transcript_formatting
"""

import asyncio

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    ActivityTranscriptFormatter,
    AgentEnvironment,
    AiohttpScenario,
    ConversationTranscriptFormatter,
    JsonTranscriptFormatter,
    print_activities,
    print_conversation,
    print_json,
)


async def init_multi_reply(env: AgentEnvironment) -> None:
    """Register an agent that sends multiple activity types."""

    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState) -> None:
        await ctx.send_activity(Activity(type=ActivityTypes.typing))
        await ctx.send_activity("Processing your request...")
        await ctx.send_activity(f"Here is your answer about: {ctx.activity.text}")


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


async def create_transcript():
    """Run the sample agent and return its transcript."""
    scenario = AiohttpScenario(init_multi_reply, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("transcript formatting")
        return client.transcript


async def demo_formatters() -> None:
    """Show the three transcript formatter outputs."""
    transcript = await create_transcript()

    section("ConversationTranscriptFormatter")
    print(ConversationTranscriptFormatter().format(transcript))

    section("ActivityTranscriptFormatter")
    print(
        ActivityTranscriptFormatter(
            model_dump_args={"exclude_unset": True, "exclude_none": True}
        ).format(transcript)
    )

    section("JsonTranscriptFormatter")
    print(
        JsonTranscriptFormatter(
            model_dump_args={"exclude_unset": True, "exclude_none": True}
        ).format(transcript)
    )


async def demo_convenience_functions() -> None:
    """Show the one-line print helpers."""
    transcript = await create_transcript()

    section("print_conversation")
    print_conversation(transcript)

    section("print_activities")
    print_activities(transcript)

    section("print_json")
    print_json(transcript)


async def main() -> None:
    print("Transcript Formatting Demo")

    await demo_formatters()
    await demo_convenience_functions()

    print(f"\n{'=' * 60}")
    print("  All transcript formatting demos complete.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
