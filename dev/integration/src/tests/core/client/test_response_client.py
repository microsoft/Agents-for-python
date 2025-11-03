from re import A
import pytest
from aiohttp import ClientSession

from microsoft_agents.activity import Activity

from src.core import ResponseClient
from ._common import DEFAULTS

class TestResponseClient:
    
    @pytest.fixture
    async def response_client(self):
        async with ResponseClient(DEFAULTS.service_url) as client:
            yield client

    @pytest.mark.asyncio
    async def test_init(self, response_client):
        assert response_client.service_endpoint == DEFAULTS.service_url

    @pytest.mark.asyncio
    async def test_endpoint(self, response_client):

        activity = Activity(type="message", text="Hello, World!")

        async with ClientSession() as session:
            async with session.post(
                f"{response_client.service_endpoint}/v3/conversations/test-conv",
                json=activity.model_dump(by_alias=True, exclude_none=True)
            ) as resp:
                assert resp.status == 200
                text = await resp.text()
                assert text == ""