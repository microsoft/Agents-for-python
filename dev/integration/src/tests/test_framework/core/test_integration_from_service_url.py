import pytest
import asyncio
import requests
from copy import copy
from aioresponses import aioresponses, CallbackResult

from src.core import integration, IntegrationFixtures


@integration(
    agent_url="http://localhost:8000/",
    service_url="http://localhost:8001/",
)
class TestIntegrationFromURL(IntegrationFixtures):

    @pytest.mark.asyncio
    async def test_service_url_integration(self, agent_client):
        """Test the integration using a service URL."""

        with aioresponses() as mocked:

            mocked.post(f"{self.agent_url}api/messages", status=200, body="Service response")

            res = await agent_client.send_activity("Hello, service!")
            assert res == "Service response"

    @pytest.mark.asyncio
    async def test_service_url_integration_with_response_side_effect(
        self, agent_client, response_client
    ):
        """Test the integration using a service URL."""

        with aioresponses() as mocked:

            def callback(url, **kwargs):
                a = requests.post(
                    f"{self.service_url}/v3/conversations/test-conv",
                    json=kwargs.get("json"),
                )
                return CallbackResult(status=200, body="Service response")

            mocked.post(f"{self.agent_url}api/messages", callback=callback)

            res = await agent_client.send_activity("Hello, service!")
            assert res == "Service response"

            await asyncio.sleep(1)

            activities = await response_client.pop()
            assert len(activities) == 1
            assert activities[0].type == "message"
            assert activities[0].text == "Hello, service!"
