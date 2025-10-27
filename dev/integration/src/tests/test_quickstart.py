import pytest

from ..core import integration_test_suite_factory, integration
from ..samples import QuickstartSample

TestSuiteBase = integration_test_suite_factory(QuickstartSample)

class TestQuickstart(TestSuiteBase):
    
    @pytest.mark.asyncio
    async def test_quickstart_functionality(self):
        pass

@integration(QuickstartSample, None) # env
class TestQuickstart:

    @pytest.mark.asyncio
    async def test_hello(self, agent_client, env):
        agent_client.send("hi")

        await asyncio.sleep(1)

        # assert env.auth...

@integration(app=None) # (endpoint="alternative")
class TestQuickstartAlternative:
    
    @pytest.mark.asyncio
    async def test_hello(self, agent_client, response_client):
        
        agent_client.send("hi")
        await asyncio.sleep(10)

        assert receiver.has_activity("hello")