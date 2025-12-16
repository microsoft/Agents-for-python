import pytest
import asyncio

from microsoft_agents.activity import Activity

from microsoft_agents.testing import (
    Integration,
    AiohttpEnvironment,
    update_with_defaults,
    AgentClient,
    ResponseClient,
    ModelQuery
)

from ...samples import QuickstartSample

class TestQuickstartBase(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment

    OUTGOING_PARENT = {
        "channel_id": "webchat",
        "locale": "en-US",
        "conversation": {"id": "conv1"},
        "from": {"id": "user1", "name": "User"},
        "recipient": {"id": "bot", "name": "Bot"},
    }

    def populate(self, input_data: dict | None = None, **kwargs) -> Activity:
        if not input_data:
            input_data = {}
        input_data.update(kwargs)
        update_with_defaults(input_data, self.OUTGOING_PARENT)
        return Activity.model_validate(input_data)
    
    @pytest.mark.asyncio
    async def test_conversation_update(self, agent_client: AgentClient, response_client: ResponseClient):

        input_activity = self.populate(
            type="conversationUpdate",
            members_added=[
                {"id": "bot-id", "name": "Bot"},
                {"id": "user1", "name": "User"},
            ],
            textFormat="plain",
            entities=[
                {
                    "type": "ClientCapabilities",
                    "requiresBotState": True,
                    "supportsTts": True
                }
            ],
            channel_data={"clientActivityId": 123}
        )

        await agent_client.send_activity(input_activity)

        await asyncio.sleep(1)  # Wait for processing

        responses = await response_client.pop()

        activity = ModelQuery(type="activity").first(responses)

        assert activity is not None
        assert "Welcome" in activity.text

    @pytest.mark.asyncio
    async def test_send_hello(self, agent_client: AgentClient, response_client: ResponseClient):

        input_activity = self.populate(
            type="message",
            text="hello",
        )

        await agent_client.send_activity(input_activity)

        await asyncio.sleep(1)  # Wait for processing

        responses = await response_client.pop()

        activity = ModelQuery(type="message").first(responses)

        assert activity is not None
        assert activity.text == "Hello!"

    @pytest.mark.asyncio
    async def test_send_hi(self, agent_client: AgentClient, response_client: ResponseClient):

        input_activity = self.populate(
            type="message",
            text="hi",
        )

        await agent_client.send_activity(input_activity)

        await asyncio.sleep(1)  # Wait for processing

        responses = await response_client.pop()
        assert len(responses) == 2

        message_activity = ModelQuery(type="message").first(responses)

        assert message_activity is not None
        assert message_activity.text == "you said: hi"

        typing_activity = ModelQuery(type="typing").first(responses)
        assert typing_activity is not None