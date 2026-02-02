from .agent_client import AgentClient

class StreamCollector:

    def __init__(self, agent_client: AgentClient):
        self._client = agent_client
        self._stream_id = None

    async def send(...):
        pass
    