import pytest
import asyncio
from copy import copy
from aioresponses import aioresponses

from src.core import (
    integration,
    IntegrationFixtures
)

@integration(service_url="http://localhost:8000/api/messages")
class TestIntegrationFromServiceURL(IntegrationFixtures):

    @pytest.mark.asyncio
    async def test_service_url_integration(self, agent_client):
        """Test the integration using a service URL."""

        with aioresponses() as mocked:

            mocked.post("http://localhost:8000/api/messages", status=200, body="Service response")

            response = await agent_client.send_activity("Hello, service!")
            assert response.status_code == 200
            assert "service" in response.text.lower()

    @pytest.mark.asyncio
    async def test_service_url_integration_with_response_side_effect(self, agent_client, response_client):
        """Test the integration using a service URL."""

        with aioresponses() as mocked:

            mocked.post("http://localhost:8000/api/messages", status=200, body="Service response")

            response = await agent_client.send_activity("Hello, service!")
            assert response.status_code == 200
            assert "service" in response.text.lower()

            await asyncio.sleep(1)

            res = await response_client.pop()
            assert len(res) == 1