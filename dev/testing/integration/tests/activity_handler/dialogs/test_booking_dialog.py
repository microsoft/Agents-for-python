# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""End-to-end integration tests for BookingDialog.

BookingDialog is a 5-step WaterfallDialog:
  1. origin      — TextPrompt
  2. destination — TextPrompt
  3. passengers  — NumberPrompt (validator: 1 ≤ n ≤ 9, retry on failure)
  4. confirm     — ConfirmPrompt showing the route summary
  5. finalize    — confirms or cancels the booking

Turn flow summary (happy path)
-------------------------------
1. User sends any message → bot asks "Where are you flying from?"
2. User sends "London"    → bot asks "Where are you flying to?"
3. User sends "Paris"     → bot asks "How many passengers? (1-9)"
4. User sends "2"         → bot shows "Route: London → Paris for 2 passenger(s). Confirm?"
5. User sends "yes"       → bot says "Booking confirmed: London to Paris for 2 passenger(s)."
"""

import pytest

from microsoft_agents.testing import (
    ActivityHandlerScenario,
    AgentClient,
    ClientConfig,
    ScenarioConfig,
    ActivityTemplate,
)

from tests.activity_handler.dialogs.sample.dialog_agent import DialogAgent
from tests.activity_handler.dialogs.sample.booking_dialog import BookingDialog

# ---------------------------------------------------------------------------
# Shared scenario
# ---------------------------------------------------------------------------

_TEMPLATE = ActivityTemplate(
    {
        "channel_id": "webchat",
        "locale": "en-US",
        "conversation": {"id": "booking-conv-1"},
        "from": {"id": "booking-user", "name": "BookingUser"},
        "recipient": {"id": "bot", "name": "Bot"},
    }
)


def _make_scenario(config: ScenarioConfig | None = None) -> ActivityHandlerScenario:
    def _create_handler(conv_state, user_state, storage):
        return DialogAgent(conv_state, user_state, BookingDialog())

    return ActivityHandlerScenario(_create_handler, config=config)


_SCENARIO = _make_scenario(
    config=ScenarioConfig(client_config=ClientConfig(activity_template=_TEMPLATE))
)


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


@pytest.mark.agent_test(_SCENARIO)
class TestBookingDialogHappyPath:
    """Full happy-path flows through BookingDialog."""

    @pytest.mark.asyncio
    async def test_full_booking_confirmed(self, agent_client: AgentClient):
        """Drive every step to completion and confirm the booking."""
        await agent_client.send("hi", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~flying from")
        agent_client.clear()

        await agent_client.send("London", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~flying to")
        agent_client.clear()

        await agent_client.send("Paris", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~passengers")
        agent_client.clear()

        await agent_client.send("2", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~London")
        agent_client.expect().that_for_any(type="message", text="~Paris")
        agent_client.expect().that_for_any(type="message", text="~2 passenger")
        agent_client.clear()

        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~confirmed")

    @pytest.mark.asyncio
    async def test_booking_cancelled_at_confirm_step(self, agent_client: AgentClient):
        """Replying 'no' at the summary step cancels the booking."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("NYC", wait=0.5)
        agent_client.clear()
        await agent_client.send("Miami", wait=0.5)
        agent_client.clear()
        await agent_client.send("1", wait=0.5)
        agent_client.clear()

        await agent_client.send("no", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~cancelled")

    @pytest.mark.asyncio
    async def test_single_passenger_accepted(self, agent_client: AgentClient):
        """Minimum (1) passenger count is accepted and echoed in the summary."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Tokyo", wait=0.5)
        agent_client.clear()
        await agent_client.send("Osaka", wait=0.5)
        agent_client.clear()

        await agent_client.send("1", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~1 passenger")
        agent_client.clear()

        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~confirmed")

    @pytest.mark.asyncio
    async def test_max_nine_passengers_accepted(self, agent_client: AgentClient):
        """Maximum (9) passenger count is accepted and appears in the final message."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Berlin", wait=0.5)
        agent_client.clear()
        await agent_client.send("Madrid", wait=0.5)
        agent_client.clear()

        await agent_client.send("9", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~9 passenger")
        agent_client.clear()

        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~9 passenger")


# ---------------------------------------------------------------------------
# Passenger validator tests
# ---------------------------------------------------------------------------


@pytest.mark.agent_test(_SCENARIO)
class TestBookingDialogPassengerValidation:
    """Tests the NumberPrompt validator that enforces 1 ≤ passengers ≤ 9."""

    @pytest.mark.asyncio
    async def test_zero_passengers_triggers_retry(self, agent_client: AgentClient):
        """Passenger count of 0 is rejected and the retry prompt is shown."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Amsterdam", wait=0.5)
        agent_client.clear()
        await agent_client.send("Brussels", wait=0.5)
        agent_client.clear()

        await agent_client.send("0", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~1 and 9")
        agent_client.clear()

        await agent_client.send("3", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~3 passenger")

    @pytest.mark.asyncio
    async def test_ten_passengers_triggers_retry(self, agent_client: AgentClient):
        """Passenger count of 10 exceeds the maximum and the retry prompt is shown."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Vienna", wait=0.5)
        agent_client.clear()
        await agent_client.send("Prague", wait=0.5)
        agent_client.clear()

        await agent_client.send("10", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~1 and 9")
        agent_client.clear()

        await agent_client.send("5", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~5 passenger")

    @pytest.mark.asyncio
    async def test_multiple_invalid_values_then_valid(
        self, agent_client: AgentClient
    ):
        """Several out-of-range values each trigger the retry prompt before a valid entry."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Rome", wait=0.5)
        agent_client.clear()
        await agent_client.send("Florence", wait=0.5)
        agent_client.clear()

        await agent_client.send("0", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~1 and 9")
        agent_client.clear()

        await agent_client.send("100", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~1 and 9")
        agent_client.clear()

        await agent_client.send("7", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~7 passenger")


# ---------------------------------------------------------------------------
# Summary content tests
# ---------------------------------------------------------------------------


@pytest.mark.agent_test(_SCENARIO)
class TestBookingDialogSummary:
    """Tests that verify the summary shown at the ConfirmPrompt step."""

    @pytest.mark.asyncio
    async def test_summary_includes_origin_and_destination(
        self, agent_client: AgentClient
    ):
        """The confirm prompt contains both origin and destination city names."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Lisbon", wait=0.5)
        agent_client.clear()
        await agent_client.send("Porto", wait=0.5)
        agent_client.clear()

        await agent_client.send("2", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~Lisbon")
        agent_client.expect().that_for_any(type="message", text="~Porto")

    @pytest.mark.asyncio
    async def test_confirmed_message_includes_full_route(
        self, agent_client: AgentClient
    ):
        """The confirmed booking message includes origin, destination, and passenger count."""
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Dublin", wait=0.5)
        agent_client.clear()
        await agent_client.send("Edinburgh", wait=0.5)
        agent_client.clear()
        await agent_client.send("4", wait=0.5)
        agent_client.clear()

        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~Dublin")
        agent_client.expect().that_for_any(type="message", text="~Edinburgh")
        agent_client.expect().that_for_any(type="message", text="~4 passenger")
