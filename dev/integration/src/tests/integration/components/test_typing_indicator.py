import pytest
import asyncio

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ChannelAccount
)

from src.core import integration, IntegrationFixtures, AiohttpEnvironment
from src.samples import QuickstartSample

@integration(sample=QuickstartSample, environment=AiohttpEnvironment)
class TestTypingIndicator(IntegrationFixtures):

    @pytest.mark.asyncio
    async def test_typing_indicator(self, agent_client, response_client):

        activity_base = Activity(
            type=ActivityTypes.message,
            from_property={"id": "user1", "name": "User 1"},
            recipient={"id": "agent", "name": "Agent"},
            conversation={"id": "conv1"},
            channel_id="test_channel"
        )

        activity_a = activity_base.model_copy()
        activity_b = activity_base.model_copy()

        activity_a.from_property = ChannelAccount(id="user1", name="User 1")
        activity_b.from_property = ChannelAccount(id="user2", name="User 2")

        await asyncio.gather(
            agent_client.send_activity(activity_a),
            agent_client.send_activity(activity_b)
        )