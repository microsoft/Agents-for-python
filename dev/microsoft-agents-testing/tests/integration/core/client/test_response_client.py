import pytest
import asyncio
from aiohttp import ClientSession

from microsoft_agents.activity import Activity
from microsoft_agents.testing import ResponseClient

from ._common import DEFAULTS


class TestResponseClient:

    @pytest.fixture
    async def response_client(self):
        async with ResponseClient(
            host=DEFAULTS.host, port=DEFAULTS.response_port
        ) as client:
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
                json=activity.model_dump(by_alias=True, exclude_none=True),
            ) as resp:
                assert resp.status == 200
                text = await resp.text()
                assert text == '{"message": "Activity received"}'

        await asyncio.sleep(0.1)  # Give some time for the server to process

        activities = await response_client.pop()
        assert len(activities) == 1
        assert activities[0].type == "message"
        assert activities[0].text == "Hello, World!"

        assert (await response_client.pop()) == []