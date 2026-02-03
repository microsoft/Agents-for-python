import pytest
from ..scenarios import load_scenario

from microsoft_agents.testing import (
    ActivityTemplate,
    AgentClient,
    ClientConfig,
    ScenarioConfig,
)

_TEMPLATE = {
    "channel_id": "webchat",
    "locale": "en-US",
    "conversation": {"id": "conv1"},
    "from": {"id": "user1", "name": "User"},
    "recipient": {"id": "bot", "name": "Bot"},
}

_SCENARIO = load_scenario("quickstart", config=ScenarioConfig(
    client_config=ClientConfig(
        activity_template=ActivityTemplate(_TEMPLATE)
    )
))

@pytest.mark.agent_test(_SCENARIO)
class TestQuickstart:
    """Integration tests for the Quickstart scenario."""

    @pytest.mark.asyncio
    async def test_conversation_update(self, agent_client: AgentClient):
        """Test sending a conversation update activity."""
        input_activity = agent_client.template.create({
            "type": "conversationUpdate",
            "members_added": [
                {"id": "bot-id", "name": "Bot"},
                {"id": "user1", "name": "User"},
            ],
            "textFormat": "plain",
            "entities": [
                {
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsTts": True
                }
            ],
            "channel_data": {"clientActivityId": 123}
        })

        await agent_client.send(input_activity, wait=1.0)
        agent_client.expect().that_for_one(type="message", text="~Welcome")

    @pytest.mark.asyncio
    async def test_send_hello(self, agent_client: AgentClient):
        """Test sending a 'hello' message and receiving a response."""
        await agent_client.send("hello", wait=1.0)
        agent_client.expect().that_for_one(type="message", text="Hello!")

    @pytest.mark.asyncio
    async def test_send_hi(self, agent_client: AgentClient):
        """Test sending a 'hi' message and receiving a response."""
    
        await agent_client.send("hi", wait=1.0)
        responses = agent_client.recent()

        assert len(responses) == 2
        assert len(agent_client.history()) == 2

        agent_client.expect().that_for_one(type="message", text="you said: hi")
        agent_client.expect().that_for_one(type="typing")