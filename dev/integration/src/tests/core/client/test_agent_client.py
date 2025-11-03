import json
from contextlib import contextmanager
import re

import pytest
from aioresponses import aioresponses
from msal import ConfidentialClientApplication

from microsoft_agents.activity import Activity

from src.core import AgentClient

from ._common import DEFAULTS

class TestAgentClient:

    @pytest.fixture
    async def agent_client(self):
        client = AgentClient(
            messaging_endpoint=DEFAULTS.messaging_endpoint,
            cid=DEFAULTS.cid,
            client_id=DEFAULTS.client_id,
            tenant_id=DEFAULTS.tenant_id,
            client_secret=DEFAULTS.client_secret,
            service_url=DEFAULTS.service_url
        )
        yield client
        await client.close()

    @pytest.fixture
    def aioresponses_mock(self):
        with aioresponses() as mocked:
            yield mocked

    @pytest.mark.asyncio
    async def test_send_activity(self, mocker, agent_client, aioresponses_mock):
        mocker.patch.object(AgentClient, 'get_access_token', return_value="mocked_token")
        mocker.patch.object(ConfidentialClientApplication, "__new__", return_value=mocker.Mock(spec=ConfidentialClientApplication))

        assert agent_client.messaging_endpoint
        aioresponses_mock.post(agent_client.messaging_endpoint, payload={"response": "Response from service"})
        
        response = await agent_client.send_activity("Hello, World!")
        data = json.loads(response)
        assert data == {"response": "Response from service"}

    @pytest.mark.asyncio
    async def test_send_expect_replies(self, mocker, agent_client, aioresponses_mock):
        mocker.patch.object(AgentClient, 'get_access_token', return_value="mocked_token")
        mocker.patch.object(ConfidentialClientApplication, "__new__", return_value=mocker.Mock(spec=ConfidentialClientApplication))

        assert agent_client.messaging_endpoint
        activities = [
            Activity(type="message", text="Response from service"),
            Activity(type="message", text="Another response"),
        ]
        aioresponses_mock.post(agent_client.messaging_endpoint, payload={
            "activities": [activity.model_dump(by_alias=True, exclude_none=True) for activity in activities],
        })
        
        replies = await agent_client.send_expect_replies("Hello, World!")
        assert len(replies) == 2
        assert replies[0].text == "Response from service"
        assert replies[1].text == "Another response"
        assert replies[0].type == replies[1].type == "message"