from contextlib import asynccontextmanager

from .agent_client import AgentClient
from .response_client import ResponseClient
from .test_client_options import TestClientOptions

class TestClient:

    def __init__(self, options: TestClientOptions):

        self._agent_client = AgentClient()
        self._response_client = ResponseClient()

        self.options = options

    @asynccontextmanager
    async def listen(self):
        async with self._response_client:
            yield

    @asynccontextmanager
    async def conversation(self, listen: bool = False):
        

    async def pop(self):
        pass