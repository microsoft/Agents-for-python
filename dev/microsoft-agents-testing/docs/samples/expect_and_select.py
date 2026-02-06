#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Expect & Select — fluent assertions and filtering on agent responses.

Features demonstrated:
  - Expect  — assert on collections with quantifiers (all, any, none, one, n).
  - Select  — filter, order, slice, and then assert on the subset.
  - Chaining — combine multiple assertions in a single statement.
  - Field matching — match by field name using kwargs.
  - Lambda predicates — match with arbitrary callables.
  - Prefix matching — use "~" prefix for substring/contains checks.
  - AgentClient helpers — client.expect() and client.select() shortcuts.

Run::

    python -m docs.samples.expect_and_select
"""

import asyncio

from microsoft_agents.activity import Activity, ActivityTypes
from microsoft_agents.hosting.core import TurnContext, TurnState
from microsoft_agents.testing import (
    AiohttpScenario,
    AgentEnvironment,
    Expect,
    Select,
)


# ---------------------------------------------------------------------------
# Agent that produces several response types
# ---------------------------------------------------------------------------

async def init_agent(env: AgentEnvironment) -> None:
    @env.agent_application.activity("message")
    async def on_message(ctx: TurnContext, state: TurnState) -> None:
        text = (ctx.activity.text or "").lower()

        if "help" in text:
            await ctx.send_activity(Activity(type=ActivityTypes.typing))
            await ctx.send_activity("I can help with:")
            await ctx.send_activity("- Questions")
            await ctx.send_activity("- Tasks")
        else:
            await ctx.send_activity(f"Echo: {ctx.activity.text}")


scenario = AiohttpScenario(init_agent, use_jwt_middleware=False)


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------

async def main() -> None:
    async with scenario.client() as client:

        # ── 1. Basic assertions with Expect ─────────────────────────

        replies = await client.send_expect_replies("Hi!")

        # that_for_any: at least one reply matches
        Expect(replies).that_for_any(text="Echo: Hi!")

        # that (alias for that_for_all): every reply matches
        Expect(replies).that(type="message")

        # that_for_none: no reply matches
        Expect(replies).that_for_none(text="Goodbye")

        # has_count: exact count
        Expect(replies).has_count(1)

        print("✓ 1. Basic Expect assertions passed")

        # ── 2. Multi-response + quantifiers ─────────────────────────

        help_replies = await client.send_expect_replies("help")

        # At least one reply contains "Questions"
        Expect(help_replies).that_for_any(text="~Questions")

        # Exactly one reply contains "Tasks"
        Expect(help_replies).that_for_one(text="~Tasks")

        # None contains "Errors"
        Expect(help_replies).that_for_none(text="~Errors")

        # Count check (typing + 3 messages = 4 activities)
        Expect(help_replies).has_count(4)

        print("✓ 2. Multi-response quantifiers passed")

        # ── 3. Lambda predicates ────────────────────────────────────

        Expect(help_replies).that_for_any(
            lambda a: a.text is not None and "help" in a.text.lower()
        )

        print("✓ 3. Lambda predicates passed")

        # ── 4. Select — filter, then assert ─────────────────────────

        # Filter to only message-type activities
        messages = Select(help_replies).where(type="message").get()
        assert len(messages) == 3  # excludes the typing indicator

        # where_not — exclude matches
        non_typing = Select(help_replies).where_not(type="typing").get()
        assert len(non_typing) == 3

        print("✓ 4. Select.where / where_not passed")

        # ── 5. Select position helpers ──────────────────────────────

        first = Select(help_replies).where(type="message").first().get()
        assert first[0].text == "I can help with:"

        last = Select(help_replies).where(type="message").last().get()
        assert last[0].text == "- Tasks"

        second = Select(help_replies).where(type="message").at(1).get()
        assert second[0].text == "- Questions"

        print("✓ 5. Select.first / last / at passed")

        # ── 6. Select → Expect pipeline ─────────────────────────────

        Select(help_replies).where(type="message").expect().that(
            lambda a: a.text is not None
        )

        print("✓ 6. Select → Expect pipeline passed")

        # ── 7. AgentClient shortcut methods ─────────────────────────

        # client.expect() builds Expect from recent response activities
        await client.send_expect_replies("test")
        client.expect().that_for_any(text="Echo: test")

        # client.expect(history=True) uses the full conversation history
        client.expect(history=True).that_for_any(text="Echo: Hi!")

        # client.select() for filtering
        msgs = client.select(history=True).where(type="message").get()
        assert len(msgs) > 0

        print("✓ 7. AgentClient.expect() / select() shortcuts passed")

        # ── 8. Chaining multiple assertions ─────────────────────────

        (
            Expect(help_replies)
            .that_for_any(text="~help")
            .that_for_any(text="~Questions")
            .that_for_none(text="~ERROR")
            .is_not_empty()
        )

        print("✓ 8. Chained assertions passed")

    print("\nAll Expect & Select examples passed.")


if __name__ == "__main__":
    asyncio.run(main())
