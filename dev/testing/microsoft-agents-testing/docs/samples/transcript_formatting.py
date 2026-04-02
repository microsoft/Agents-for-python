#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Transcript Formatting — visualise agent conversations for debugging.

Features demonstrated:
  - Transcript / Exchange — automatic recording of every request & response.
  - ConversationTranscriptFormatter — chat-style view with custom labels.
  - ActivityTranscriptFormatter     — field-level view with selectable columns.
  - DetailLevel (MINIMAL → FULL)    — control how much context is printed.
  - TimeFormat (CLOCK / RELATIVE / ELAPSED) — timestamp display styles.
  - print_conversation / print_activities   — one-liner convenience functions.

Run::

    python -m docs.samples.transcript_formatting
"""

import asyncio

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    ConversationTranscriptFormatter,
    ActivityTranscriptFormatter,
    DetailLevel,
)
from microsoft_agents.testing.transcript_formatter import (
    TimeFormat,
    print_conversation,
    print_activities,
    DEFAULT_ACTIVITY_FIELDS,
    EXTENDED_ACTIVITY_FIELDS,
)


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

async def init_echo(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def h(ctx: TurnContext, state: TurnState):
        await ctx.send_activity(f"Echo: {ctx.activity.text}")


async def init_multi_reply(env: AgentEnvironment) -> None:
    """Agent that sends a typing indicator then multiple messages."""
    @env.agent_application.activity("message")
    async def h(ctx: TurnContext, state: TurnState):
        await ctx.send_activity(Activity(type=ActivityTypes.typing))
        await ctx.send_activity("Processing your request...")
        await ctx.send_activity(f"Here is your answer about: {ctx.activity.text}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# Demos
# ---------------------------------------------------------------------------

async def demo_detail_levels() -> None:
    """Show every DetailLevel with the ConversationTranscriptFormatter."""
    section("ConversationTranscriptFormatter — Detail Levels")

    scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("Hello!")
        await client.send_expect_replies("How are you?")
        await client.send_expect_replies("Goodbye")
        transcript = client.transcript

    for level in DetailLevel:
        print(f"\n--- {level.name} ---")
        ConversationTranscriptFormatter(detail=level).print(transcript)


async def demo_custom_labels() -> None:
    """ConversationTranscriptFormatter with custom labels."""
    section("Custom Labels (User ↔ Bot)")

    scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("ping")
        await client.send_expect_replies("pong")
        transcript = client.transcript

    ConversationTranscriptFormatter(
        user_label="Human",
        agent_label="Bot",
    ).print(transcript)


async def demo_time_formats() -> None:
    """Show CLOCK, RELATIVE, and ELAPSED timestamp styles."""
    section("TimeFormat — CLOCK / RELATIVE / ELAPSED")

    scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("First")
        await client.send_expect_replies("Second")
        await client.send_expect_replies("Third")
        transcript = client.transcript

    for tf in TimeFormat:
        print(f"\n--- {tf.name} ---")
        ConversationTranscriptFormatter(
            detail=DetailLevel.DETAILED,
            time_format=tf,
        ).print(transcript)


async def demo_activity_formatter() -> None:
    """ActivityTranscriptFormatter with selectable field columns."""
    section("ActivityTranscriptFormatter — Selectable Fields")

    scenario = AiohttpScenario(init_multi_reply, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("quantum physics")
        transcript = client.transcript

    print(f"\n--- Default fields: {DEFAULT_ACTIVITY_FIELDS} ---")
    ActivityTranscriptFormatter().print(transcript)

    print(f"\n--- Minimal (type + text only) ---")
    ActivityTranscriptFormatter(fields=["type", "text"]).print(transcript)

    print(f"\n--- Extended fields with timing ---")
    ActivityTranscriptFormatter(
        fields=EXTENDED_ACTIVITY_FIELDS,
        detail=DetailLevel.DETAILED,
    ).print(transcript)

    print(f"\n--- FULL detail ---")
    ActivityTranscriptFormatter(detail=DetailLevel.FULL).print(transcript)


async def demo_show_other_types() -> None:
    """Toggle visibility of non-message activities (e.g. typing)."""
    section("show_other_types — Typing Indicators")

    scenario = AiohttpScenario(init_multi_reply, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("test")
        transcript = client.transcript

    print("\n--- show_other_types=False (default) ---")
    ConversationTranscriptFormatter(show_other_types=False).print(transcript)

    print("\n--- show_other_types=True ---")
    ConversationTranscriptFormatter(show_other_types=True).print(transcript)


async def demo_convenience_functions() -> None:
    """print_conversation() and print_activities() one-liners."""
    section("Convenience Functions")

    scenario = AiohttpScenario(init_echo, use_jwt_middleware=False)
    async with scenario.client() as client:
        await client.send_expect_replies("Quick test")
        transcript = client.transcript

    print("\n--- print_conversation() ---")
    print_conversation(transcript)

    print("\n--- print_conversation(detail=FULL) ---")
    print_conversation(transcript, detail=DetailLevel.FULL)

    print("\n--- print_activities() ---")
    print_activities(transcript)

    print("\n--- print_activities(fields=['type', 'text', 'id']) ---")
    print_activities(transcript, fields=["type", "text", "id"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    print("Transcript Formatting Demo")
    print("Shows how conversations look with each formatter and option.\n")

    await demo_detail_levels()
    await demo_custom_labels()
    await demo_time_formats()
    await demo_activity_formatter()
    await demo_show_other_types()
    await demo_convenience_functions()

    print(f"\n{'=' * 60}")
    print("  All transcript formatting demos complete.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
