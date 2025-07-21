from typing import Protocol

from microsoft.agents.activity import AgentsModel, Activity, InvokeResponse


class ChannelProtocol(Protocol):
    async def post_activity(
        self,
        to_agent_id: str,
        to_agent_resource: str,
        endpoint: str,
        service_url: str,
        conversation_id: str,
        activity: Activity,
        *,
        response_body_type: type[AgentsModel] = None,
        **kwargs,
    ) -> InvokeResponse:
        raise NotImplementedError()
