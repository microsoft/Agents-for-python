import pytest
import asyncio

from ..core import integration


@integration(service_url="http://localhost:3978/api/messages")
class TestQuickstart:

    @pytest.mark.asyncio
    async def test_quickstart_functionality(self, agent_client, response_client):
        await agent_client.send("hi")
        await asyncio.sleep(2)
        response = (await response_client.pop())[0]
        assert "hello" in response.text.lower()


# class TestQuickstart(TestSuiteBase):

#     @pytest.mark.asyncio
#     async def test_quickstart_functionality(self):
#         pass

# @integration(QuickstartSample, None) # env
# class TestQuickstart:

#     @pytest.mark.asyncio
#     async def test_hello(self, agent_client, env):
#         agent_client.send("hi")

#         await asyncio.sleep(1)

#         # assert env.auth...

# @integration(app=None) # (endpoint="alternative")
# class TestQuickstartAlternative:

#     @pytest.mark.asyncio
#     async def test_hello(self, agent_client, response_client):

#         agent_client.send("hi")
#         await asyncio.sleep(10)

#         assert receiver.has_activity("hello")
