from typing import Protocol

from microsoft_agents.activity import Activity

class AgentClientProtocol(Protocol):

    async def send_request(self, activity: Activity) -> str:
        ...

    async def send_activity(self, activity: Activity) -> list[Activity]:
        ...

    async def send_expect_replies_activity(self, activity: Activity) -> list[Activity]:
        ...

    async def send_invoke_activity(self, activity: Activity) -> str:
        ...