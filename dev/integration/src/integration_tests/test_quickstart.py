import pytest
from src.core import integration, IntegrationFixtures, AiohttpEnvironment
from src.samples import QuickstartSample

@integration(sample=QuickstartSample, environment=AiohttpEnvironment)
class TestQuickstartSample(IntegrationFixtures):

    @pytest.mark.asyncio
    async def test_welcome_message(self, sample, environment, agent_client, response_client):
        response = await self.client.send_message("", members_added=["user1"])
        assert "Welcome to the empty agent!" in response.activities[0].text