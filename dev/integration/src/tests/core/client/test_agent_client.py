import pytest
from aioresponses import aioresponses

from src.core import AgentClient

class TestAgentClient:

    @pytest.fixture
    def agent_client(self) -> AgentClient:
        return AgentClient(base_url="")
    
    @pytest.fixture
    async def service_url(self):
        with aioresponses() as mocked:
            mocked.get("https://example.com/service-url", payload={"serviceUrl": "https://service.example.com"})
            client = AgentClient(base_url="https://example.com")
            service_url = await client.get_service_url()
            yield service_url