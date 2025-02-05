from typing import Protocol

from microsoft.agents.core.models import Activity, InvokeResponse


class ChannelProtocol(Protocol):
    async def post_activity(
        self,
        to_bot_id: str,
        to_bot_resource: str,
        endpoint: str,
        service_url: str,
        conversation_id: str,
        activity: Activity,
    ) -> InvokeResponse:
        raise NotImplementedError()
