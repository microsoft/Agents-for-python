from typing import AsyncContextManager

from .test_client import TestClient

class SampleAgentScenario:

    async def _init_agent_application(self):
        pass

    async def _init_agent(self):
        pass

    async def run(self) -> AsyncContextManager[TestClient]:
        
        async with TestServer(self._application) as server:
            client = TestClient(server.url)
            yield client