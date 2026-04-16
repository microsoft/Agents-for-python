# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""End-to-end integration tests for UserProfileDialog.

These tests drive the full 7-step WaterfallDialog (transport → name →
name_confirm → age → picture → summary → confirm) through a real in-process
aiohttp server.  No external credentials are needed; state is held in
MemoryStorage.

Turn flow summary
-----------------
1.  User sends any message → bot asks for transport choice (Car/Bus/Bicycle)
2.  User picks "Car"        → bot asks for name
3.  User sends "Alice"      → bot says "Thanks Alice", asks for age confirmation
4.  User sends "yes"        → bot asks for age (with validator: 0 < age < 150)
5.  User sends "25"         → bot says "I have your age as 25.", asks for picture
6.  User sends any text     → picture validator accepts the no-attachment case,
                              bot sends summary + "Is this ok?"
7.  User sends "yes"        → bot saves profile, says "Thanks. Your profile was saved"
"""

import pytest

from microsoft_agents.testing import AgentClient, ScenarioConfig, ClientConfig, ActivityTemplate

from tests.scenarios import create_dialog_scenario

# ---------------------------------------------------------------------------
# Shared activity template — identifies the test user and conversation
# ---------------------------------------------------------------------------
_TEMPLATE = ActivityTemplate(
    {
        "channel_id": "webchat",
        "locale": "en-US",
        "conversation": {"id": "dialog-conv-1"},
        "from": {"id": "user1", "name": "Alice"},
        "recipient": {"id": "bot", "name": "Bot"},
    }
)

_SCENARIO = create_dialog_scenario(
    config=ScenarioConfig(
        client_config=ClientConfig(activity_template=_TEMPLATE),
    )
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.agent_test(_SCENARIO)
class TestUserProfileDialogHappyPath:
    """Full happy-path walk-through of UserProfileDialog."""

    @pytest.mark.asyncio
    async def test_full_flow_save_profile(self, agent_client: AgentClient):
        """Drive every step to completion and confirm the profile is saved."""

        # Turn 1 — start dialog, expect transport prompt
        await agent_client.send("hi", wait=0.5)
        agent_client.expect().that_for_any(
            type="message", text="~mode of transport"
        )
        agent_client.clear()

        # Turn 2 — pick a transport, expect name prompt
        await agent_client.send("Car", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~name")
        agent_client.clear()

        # Turn 3 — provide name, expect thanks + age-confirmation prompt
        await agent_client.send("Alice", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~Thanks Alice")
        agent_client.expect().that_for_any(type="message", text="~age")
        agent_client.clear()

        # Turn 4 — confirm age ("yes"), expect age-number prompt
        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~enter your age")
        agent_client.clear()

        # Turn 5 — provide valid age, expect age acknowledgement + picture prompt
        await agent_client.send("25", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~age as 25")
        agent_client.expect().that_for_any(type="message", text="~profile picture")
        agent_client.clear()

        # Turn 6 — skip picture (plain text message, no attachment)
        # picture_prompt_validator returns True even without attachments
        await agent_client.send("skip", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~No attachments")
        agent_client.expect().that_for_any(type="message", text="~Is this ok")
        agent_client.clear()

        # Turn 7 — confirm save
        await agent_client.send("yes", wait=0.5)
        agent_client.expect().that_for_any(
            type="message", text="~profile was saved"
        )

    @pytest.mark.asyncio
    async def test_full_flow_discard_profile(self, agent_client: AgentClient):
        """Walk through all steps but decline to save at the end."""

        await agent_client.send("hi", wait=0.5)
        agent_client.clear()

        await agent_client.send("Bus", wait=0.5)
        agent_client.clear()

        await agent_client.send("Bob", wait=0.5)
        agent_client.clear()

        # skip age
        await agent_client.send("no", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~No age given")
        agent_client.clear()

        # skip picture
        await agent_client.send("skip", wait=0.5)
        agent_client.clear()

        # decline to save
        await agent_client.send("no", wait=0.5)
        agent_client.expect().that_for_any(
            type="message", text="~will not be kept"
        )


@pytest.mark.agent_test(_SCENARIO)
class TestUserProfileDialogValidation:
    """Tests that cover validator-rejection paths."""

    @pytest.mark.asyncio
    async def test_age_validator_rejects_out_of_range(self, agent_client: AgentClient):
        """An age ≤ 0 or ≥ 150 triggers the retry prompt."""

        # Start dialog through to the age-number prompt
        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Car", wait=0.5)
        agent_client.clear()
        await agent_client.send("Alice", wait=0.5)
        agent_client.clear()
        await agent_client.send("yes", wait=0.5)  # confirm age prompt
        agent_client.clear()

        # Send invalid age
        await agent_client.send("200", wait=0.5)
        agent_client.expect().that_for_any(
            type="message", text="~greater than 0 and less than 150"
        )
        agent_client.clear()

        # Send another invalid age
        await agent_client.send("0", wait=0.5)
        agent_client.expect().that_for_any(
            type="message", text="~greater than 0 and less than 150"
        )
        agent_client.clear()

        # Valid age accepted
        await agent_client.send("30", wait=0.5)
        agent_client.expect().that_for_any(type="message", text="~age as 30")

    @pytest.mark.asyncio
    async def test_skip_age_goes_directly_to_picture_step(self, agent_client: AgentClient):
        """Answering 'no' to the age-confirmation question skips NumberPrompt."""

        await agent_client.send("hi", wait=0.5)
        agent_client.clear()
        await agent_client.send("Bicycle", wait=0.5)
        agent_client.clear()
        await agent_client.send("Carol", wait=0.5)
        agent_client.clear()

        # Decline age
        await agent_client.send("no", wait=0.5)
        # Should jump straight to picture step (age = -1 → "No age given.")
        agent_client.expect().that_for_any(type="message", text="~No age given")
        agent_client.expect().that_for_any(type="message", text="~profile picture")
