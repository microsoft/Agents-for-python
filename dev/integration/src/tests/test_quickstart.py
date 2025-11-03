import pytest
import asyncio

from src.core import integration, IntegrationFixtures, AiohttpEnvironment
from src.samples import QuickstartSample

@integration(sample=QuickstartSample, environment=AiohttpEnvironment)
class TestQuickstart(IntegrationFixtures):

    @pytest.mark.asyncio
    async def test_welcome_message(self, agent_client, response_client):
        await agent_client.send_expect_replies("hi")