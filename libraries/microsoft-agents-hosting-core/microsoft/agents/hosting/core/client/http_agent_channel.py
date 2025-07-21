from copy import deepcopy, copy

from aiohttp import ClientSession
from microsoft.agents.hosting.core.authorization import AccessTokenProviderBase
from microsoft.agents.activity import (
    AgentsModel,
    Activity,
    ConversationReference,
    ChannelAccount,
    InvokeResponse,
    RoleTypes,
)

from .channel_protocol import ChannelProtocol
from .conversation_constants import ConversationConstants


class HttpAgentChannel(ChannelProtocol):
    def __init__(self, token_access: AccessTokenProviderBase) -> None:
        self._token_access = token_access

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
        if not endpoint:
            raise ValueError("HttpAgentChannel.post_activity: Endpoint is required")
        if not service_url:
            raise ValueError("HttpAgentChannel.post_activity: Service URL is required")
        if not conversation_id:
            raise ValueError(
                "HttpAgentChannel.post_activity: Conversation ID is required"
            )
        if not activity:
            raise ValueError("HttpAgentChannel.post_activity: Activity is required")

        activity_copy = deepcopy(activity)

        # TODO: should conversation should be a deep copy instead of shallow?
        activity_copy.relates_to = ConversationReference(
            service_url=service_url,
            activity_id=activity_copy.id,
            channel_id=activity_copy.channel_id,
            locale=activity_copy.locale,
            conversation=copy(activity_copy.conversation),
        )

        activity_copy.conversation.id = conversation_id
        activity_copy.service_url = service_url
        activity_copy.recipient = activity_copy.recipient or ChannelAccount()
        activity_copy.recipient.role = RoleTypes.skill

        token_result = await self._token_access.get_access_token(
            to_agent_resource, [f"{to_agent_id}/.default"]
        )
        headers = {
            "Authorization": f"Bearer {token_result}",
            "Content-Type": "application/json",
            ConversationConstants.CONVERSATION_ID_HTTP_HEADER_NAME: conversation_id,
        }

        async with ClientSession() as session:
            async with session.post(
                endpoint,
                headers=headers,
                json=activity_copy.model_dump(
                    mode="json", by_alias=True, exclude_unset=True
                ),
            ) as response:
                content = None
                if response.ok:
                    try:
                        content = await response.json()
                    except:
                        pass
                    if response_body_type:
                        content = response_body_type.model_validate(content)

                    return InvokeResponse(status=response.status, body=content)

                else:
                    # TODO: Log error
                    # TODO: Fix generic AgentsModel serialization
                    if response.content_type == "application/json":
                        content = await response.json()
                    elif response.content_type == "text/plain":
                        content = await response.text()

                    return InvokeResponse(status=response.status, body=content)
