import pytest

from microsoft_agents.hosting.core import (
    RestChannelServiceClientFactory,
)

class TestRestChannelServiceClientFactory:
    
    @pytest.mark.asyncio
    def test_create_connector_client(self):
        
        factory = RestChannelServiceClientFactory()
        client = factory.create_connector_client("http://example.com")
        assert client is not None
        assert client.base_url == "http://example.com"