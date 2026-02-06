# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""
Intentionally failing tests to preview assertion and transcript formatting.

Run with:
    pytest tests/test_failure_formatting.py -v --tb=long -s -m failure_demo

These tests are NOT part of the normal test suite — they are all expected
to fail.  They are marked with @pytest.mark.failure_demo so they only run
when you explicitly request them:  pytest -m failure_demo
"""

import pytest

# Skip every test in this module unless '-m failure_demo' is passed
pytestmark = pytest.mark.failure_demo

from microsoft_agents.hosting.core import TurnContext, TurnState

from microsoft_agents.testing.aiohttp_scenario import AiohttpScenario, AgentEnvironment
from microsoft_agents.testing.core.fluent import Expect, Select
from microsoft_agents.testing.transcript_formatter import (
    ConversationTranscriptFormatter,
    ActivityTranscriptFormatter,
    DetailLevel,
    TimeFormat,
)


# ============================================================================
# Agent setup
# ============================================================================


async def init_echo_agent(env: AgentEnvironment) -> None:
    """Echo agent — replies with 'Echo: <text>'."""
    @env.agent_application.activity("message")
    async def on_message(context: TurnContext, state: TurnState):
        await context.send_activity(f"Echo: {context.activity.text}")


echo_scenario = AiohttpScenario(
    init_agent=init_echo_agent,
    use_jwt_middleware=False,
)


# ============================================================================
# 1. Expect — that_for_any with wrong text (no match)
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectThatForAny:

    @pytest.mark.asyncio
    async def test_FAIL_wrong_text_any(self, agent_client):
        """Expect.that_for_any fails when no activity has the expected text."""
        await agent_client.send_expect_replies("Hello!")
        # The agent replies "Echo: Hello!" — asserting a different text fails
        agent_client.expect().that_for_any(text="Goodbye!")


# ============================================================================
# 2. Expect — that (for_all) when only some match
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectThatForAll:

    @pytest.mark.asyncio
    async def test_FAIL_not_all_match(self, agent_client):
        """Expect.that fails when not all activities match."""
        await agent_client.send_expect_replies("AAA")
        await agent_client.send_expect_replies("BBB")
        # Only one has text "Echo: AAA" — asserting all match fails
        agent_client.expect(history=True).that(text="Echo: AAA")


# ============================================================================
# 3. Expect — that_for_none when some match
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectThatForNone:

    @pytest.mark.asyncio
    async def test_FAIL_some_match_unexpectedly(self, agent_client):
        """Expect.that_for_none fails when an activity does match."""
        await agent_client.send_expect_replies("Hello!")
        # The response IS "Echo: Hello!" — asserting none match fails
        agent_client.expect().that_for_none(text="Echo: Hello!")


# ============================================================================
# 4. Expect — that_for_one when zero or multiple match
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectThatForOne:

    @pytest.mark.asyncio
    async def test_FAIL_zero_match(self, agent_client):
        """Expect.that_for_one fails when zero activities match."""
        await agent_client.send_expect_replies("Hello!")
        agent_client.expect().that_for_one(text="does not exist")


# ============================================================================
# 5. Expect — count mismatch (has_count)
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectCount:

    @pytest.mark.asyncio
    async def test_FAIL_wrong_count(self, agent_client):
        """Expect.has_count fails when count differs."""
        await agent_client.send_expect_replies("Hello!")
        # Agent sends 1 reply, but we assert 5
        agent_client.expect().has_count(5)


# ============================================================================
# 6. Expect — is_empty on non-empty
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectIsEmpty:

    @pytest.mark.asyncio
    async def test_FAIL_not_empty(self, agent_client):
        """Expect.is_empty fails when there are activities."""
        await agent_client.send_expect_replies("Hello!")
        agent_client.expect().is_empty()


# ============================================================================
# 7. Expect — that_for_any with lambda predicate
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectLambda:

    @pytest.mark.asyncio
    async def test_FAIL_lambda_predicate(self, agent_client):
        """Expect fails with a lambda predicate that no item satisfies."""
        await agent_client.send_expect_replies("Hello!")
        agent_client.expect().that_for_any(
            lambda a: a.text is not None and len(a.text) > 1000
        )


# ============================================================================
# 8. Expect — multiple field checks, partial failure
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_ExpectMultiField:

    @pytest.mark.asyncio
    async def test_FAIL_partial_field_match(self, agent_client):
        """Expect fails showing which field checks passed vs failed."""
        await agent_client.send_expect_replies("Hello!")
        # type="message" is correct, but text is wrong
        agent_client.expect().that_for_any(
            type="message",
            text="NOPE",
        )


# ============================================================================
# 9. Transcript formatting on failure — Conversation view
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_TranscriptConversation:

    @pytest.mark.asyncio
    async def test_FAIL_with_conversation_transcript(self, agent_client):
        """Fails and prints the conversation transcript for review."""
        await agent_client.send_expect_replies("Hello!")
        await agent_client.send_expect_replies("How are you?")
        await agent_client.send_expect_replies("Tell me a joke")

        # Print conversation before the failing assertion
        fmt = ConversationTranscriptFormatter(detail=DetailLevel.DETAILED)
        print("\n--- Conversation Transcript (DETAILED) ---")
        fmt.print(agent_client.transcript)
        print("--- End Transcript ---\n")

        agent_client.expect(history=True).that_for_any(text="a]joke")


# ============================================================================
# 10. Transcript formatting on failure — Activity view
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_TranscriptActivity:

    @pytest.mark.asyncio
    async def test_FAIL_with_activity_transcript(self, agent_client):
        """Fails and prints the activity transcript for review."""
        await agent_client.send_expect_replies("Start")
        await agent_client.send_expect_replies("Middle")
        await agent_client.send_expect_replies("End")

        fmt = ActivityTranscriptFormatter(detail=DetailLevel.FULL)
        print("\n--- Activity Transcript (FULL) ---")
        fmt.print(agent_client.transcript)
        print("--- End Transcript ---\n")

        agent_client.expect(history=True).that(text="ALL_SAME")


# ============================================================================
# 11. Transcript formatting — all detail levels side by side
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_TranscriptDetailLevels:

    @pytest.mark.asyncio
    async def test_FAIL_all_detail_levels(self, agent_client):
        """Shows all transcript detail levels then fails."""
        await agent_client.send_expect_replies("Alpha")
        await agent_client.send_expect_replies("Beta")

        for level in DetailLevel:
            fmt = ConversationTranscriptFormatter(detail=level)
            print(f"\n--- Conversation: {level.value} ---")
            fmt.print(agent_client.transcript)

        for level in DetailLevel:
            fmt = ActivityTranscriptFormatter(detail=level)
            print(f"\n--- Activity: {level.value} ---")
            fmt.print(agent_client.transcript)

        print()
        assert False, "Intentional failure — review transcript output above."


# ============================================================================
# 12. Transcript formatting — time format variants
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_TranscriptTimeFormats:

    @pytest.mark.asyncio
    async def test_FAIL_time_formats(self, agent_client):
        """Shows transcript with each TimeFormat then fails."""
        await agent_client.send_expect_replies("First")
        await agent_client.send_expect_replies("Second")
        await agent_client.send_expect_replies("Third")

        for tf in TimeFormat:
            fmt = ConversationTranscriptFormatter(
                detail=DetailLevel.DETAILED,
                time_format=tf,
            )
            print(f"\n--- TimeFormat: {tf.value} ---")
            fmt.print(agent_client.transcript)

        print()
        assert False, "Intentional failure — review time format output above."


# ============================================================================
# 13. Select + Expect pipeline failure
# ============================================================================


@pytest.mark.agent_test(echo_scenario)
class TestFAIL_SelectExpect:

    @pytest.mark.asyncio
    async def test_FAIL_select_then_expect(self, agent_client):
        """Select filters correctly, then Expect fails on the subset."""
        await agent_client.send_expect_replies("Hello!")

        responses = agent_client._collect(history=True)
        Select(responses).where(type="message").expect().that(text="wrong answer")
