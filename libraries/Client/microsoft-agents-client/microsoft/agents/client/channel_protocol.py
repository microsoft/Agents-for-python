from typing import Protocol

from microsoft.agents.core.models import AgentsModel, Activity, InvokeResponse


class ChannelProtocol(Protocol):
    async def post_activity(
        self,
        to_bot_id: str,
        to_bot_resource: str,
        endpoint: str,
        service_url: str,
        conversation_id: str,
        activity: Activity,
        *,
        response_body_type: type[AgentsModel] = None,
        **kwargs,
    ) -> InvokeResponse:
        raise NotImplementedError()
