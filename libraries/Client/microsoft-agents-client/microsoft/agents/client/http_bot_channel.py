from aiohttp import ClientSession
from microsoft.agents.authentication import AccessTokenProviderBase
from microsoft.agents.core.models import Activity

from .channel_protocol import ChannelProtocol


class HttpBotChannel(ChannelProtocol):
    def __init__(self, token_access: AccessTokenProviderBase) -> None:
        self._token_access = token_access

    async def post_activity(
        self,
        to_bot_id: str,
        to_bot_resource: str,
        endpoint: str,
        service_url: str,
        conversation_id: str,
        activity: Activity,
    ) -> dict:
        if not endpoint:
            raise ValueError("HttpBotChannel.post_activity: Endpoint is required")
        if not service_url:
            raise ValueError("HttpBotChannel.post_activity: Service URL is required")
        if not conversation_id:
            raise ValueError(
                "HttpBotChannel.post_activity: Conversation ID is required"
            )
