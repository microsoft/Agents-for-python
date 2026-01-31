from typing_extensions import Self

from .core import AgentClient, Expect

class AssertResponses:
    def __init__(self, agent_client: AgentClient):
        self._agent_client = agent_client

    def ends_conversation(self) -> Self:
        """
        Check if the response indicates the end of a conversation.
        """
        res = self._agent_client.recent()
        Expect(res).that_for_any()
        return self