import pytest
import asyncio

from src.core import IntegrationFixtures, AiohttpEnvironment
from src.samples import QuickstartSample

class TestQuickstart(Integration):
    _sample_cls = QuickstartSample
    _environment_cls = AiohttpEnvironment

    @pytest.mark.asyncio
    async def test_welcome_message(self, agent_client, response_client):
        res = await agent_client.send_expect_replies("hi")
        await asyncio.sleep(1)  # Wait for processing
        responses = await response_client.pop()

        assert len(responses) == 0

        first_non_typing = next((r for r in res if r.type != "typing"), None)
        assert first_non_typing is not None
        assert first_non_typing.text == "you said: hi"