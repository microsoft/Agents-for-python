import pytest
from aioresponses import aioresponses

from src.core import AgentClient

class TestAgentClient:

    @pytest.fixture
    def agent_client(self) -> AgentClient:
        return AgentClient(base_url="")
    
    @pytest.fixture
    def mock_service(self):

        async def context_manager():
            with aioresponses() as mocked:
                mocked.get("https://example.com/service-url", payload={"serviceUrl": "https://service.example.com"})
                client = AgentClient(base_url="https://example.com")
                service_url = await client.get_service_url()
                yield service_url

        return context_manager

    @pytest.mark.asyncio
    async def test_get_service_url(self, agent_client: AgentClient, service_url: str):
        assert service_url == "https://service.example.com"

    @pytest.mark.asyncio
    async def test_send_activity(self, agent_client, mock_service):
        with mock_service as service_url:
            response = await agent_client.send_activity("Hello, World!")
            assert response == "Response from service"