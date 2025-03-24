from typing import Optional
from uuid import uuid4

from aiohttp.web import HTTPException

from microsoft.agents.core import ChannelAdapterProtocol, TurnContextProtocol
from microsoft.agents.core.models import (
    ActivityTypes,
    Activity,
    CallerIdConstants,
    ChannelAccount,
    ResourceResponse,
    AttachmentData,
    PagedMembersResult,
    Transcript,
    ConversationParameters,
    ConversationResourceResponse,
    ConversationsResult,
)
from microsoft.agents.authorization import ClaimsIdentity
from microsoft.agents.client import (
    ChannelHostProtocol,
    ChannelInfoProtocol,
    ConversationIdFactoryProtocol,
    ConversationIdFactoryOptions,
)
from microsoft.agents.builder import (
    ActivityHandler,
    ChannelApiHandlerProtocol,
    ChannelAdapter,
)


class Agent1(ActivityHandler, ChannelApiHandlerProtocol):
    _active_agent_client = False

    def __init__(
        self,
        adapter: ChannelAdapterProtocol,
        channel_host: ChannelHostProtocol,
        conversation_id_factory: ConversationIdFactoryProtocol,
    ):
        if not adapter:
            raise ValueError("Agent1.__init__(): adapter cannot be None")
        if not channel_host:
            raise ValueError("Agent1.__init__(): channel_host cannot be None")
        if not conversation_id_factory:
            raise ValueError(
                "Agent1.__init__(): conversation_id_factory cannot be None"
            )

        self._adapter = adapter
        self._channel_host = channel_host
        self._conversation_id_factory = conversation_id_factory

        target_a2a_id = "EchoAgent"
        self._target_a2a = self._channel_host.channels.get(target_a2a_id)

    async def on_turn(self, turn_context: TurnContextProtocol):
        # Forward all activities except EndOfConversation to the A2A connection
        if turn_context.activity.type != ActivityTypes.end_of_conversation:
            # Try to get the active A2A connection
            if Agent1._active_agent_client:
                await self._send_to_agent(turn_context, self._target_a2a)
                return

        await super().on_turn(turn_context)

    # update when doing activity type protocols
    async def on_message_activity(self, turn_context: TurnContextProtocol):
        if "agent" in turn_context.activity.text.lower():
            # TODO: review activity | str interface for send_activity
            await turn_context.send_activity("Got it, connecting you to the agent...")

            Agent1._active_agent_client = True

            # send to agent
            await self._send_to_agent(turn_context, self._target_a2a)
            return

        await turn_context.send_activity('Say "agent" and I\'ll patch you through')

    async def on_end_of_conversation_activity(self, turn_context: TurnContextProtocol):
        # Clear the active A2A connection
        Agent1._active_agent_client = False

        # Show status message, text and value returned by the A2A connection
        eoc_activity_message = f"Received {turn_context.activity.type}. Code: {turn_context.activity.code}."
        if turn_context.activity.text:
            eoc_activity_message += f" Text: {turn_context.activity.text}"

        if turn_context.activity.value:
            eoc_activity_message += f" Value: {turn_context.activity.value}"

        await turn_context.send_activity(eoc_activity_message)
        await turn_context.send_activity(
            'Back in the root agent. Say "agent" and I\'ll patch you through'
        )

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContextProtocol
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    'Hello and welcome! Say "agent" and I\'ll patch you through'
                )

    """
    ChannelApiHandler protocol
    """

    async def on_get_conversations(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        continuation_token: Optional[str] = None,
    ) -> ConversationsResult:
        pass

    async def on_create_conversation(
        self, claims_identity: ClaimsIdentity, parameters: ConversationParameters
    ) -> ConversationResourceResponse:
        pass

    async def on_send_to_conversation(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity: Activity
    ) -> ResourceResponse:
        return await self._process_activity(
            claims_identity, conversation_id, None, activity
        )

    async def on_send_conversation_history(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        transcript: Transcript,
    ) -> ResourceResponse:
        pass

    async def on_update_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
    ) -> ResourceResponse:
        pass

    async def on_reply_to_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        activity_id: str,
        activity: Activity,
    ) -> ResourceResponse:
        return await self._process_activity(
            claims_identity, conversation_id, activity_id, activity
        )

    async def on_delete_activity(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity_id: str
    ):
        pass

    async def on_get_conversation_members(
        self, claims_identity: ClaimsIdentity, conversation_id: str
    ) -> list[ChannelAccount]:
        pass

    async def on_get_conversation_member(
        self, claims_identity: ClaimsIdentity, user_id: str, conversation_id: str
    ) -> ChannelAccount:
        pass

    async def on_get_conversation_paged_members(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        page_size: Optional[int] = None,
        continuation_token: Optional[str] = None,
    ) -> PagedMembersResult:
        pass

    async def on_delete_conversation_member(
        self, claims_identity: ClaimsIdentity, conversation_id: str, member_id: str
    ):
        pass

    async def on_get_activity_members(
        self, claims_identity: ClaimsIdentity, conversation_id: str, activity_id: str
    ) -> list[ChannelAccount]:
        pass

    async def on_upload_attachment(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        attachment_upload: AttachmentData,
    ) -> ResourceResponse:
        pass

    async def _send_to_agent(
        self, turn_context: TurnContextProtocol, target_channel: ChannelInfoProtocol
    ):
        # Create a conversation ID to communicate with the A2A connection
        options = ConversationIdFactoryOptions(
            from_oauth_scope=turn_context.turn_state.get(
                ChannelAdapter.OAUTH_SCOPE_KEY
            ),
            from_agent_id=self._channel_host.host_app_id,
            activity=turn_context.activity,
            agent=target_channel,
        )

        conversation_id = await self._conversation_id_factory.create_conversation_id(
            options
        )

        # TODO: might need to close connection, tbd
        channel = self._channel_host.get_channel_from_channel_info(target_channel)

        # Route activity to the A2A connection
        response = await channel.post_activity(
            target_channel.app_id,
            target_channel.resource_url,
            target_channel.endpoint,
            self._channel_host.host_endpoint,
            conversation_id,
            turn_context.activity,
        )

        if response.status < 200 or response.status >= 300:
            raise HTTPException(
                text=f'Error invoking the id: "{target_channel.id}" at "{target_channel.endpoint}" (status is {response.status}). \r\n {response.body}'
            )

    @staticmethod
    def _apply_activity_to_turn_context(
        turn_context: TurnContextProtocol, activity: Activity
    ):
        # TODO: activity.properties?
        turn_context.activity.channel_data = activity.channel_data
        turn_context.activity.code = activity.code
        turn_context.activity.entities = activity.entities
        turn_context.activity.locale = activity.locale
        turn_context.activity.local_timestamp = activity.local_timestamp
        turn_context.activity.name = activity.name
        turn_context.activity.relates_to = activity.relates_to
        turn_context.activity.reply_to_id = activity.reply_to_id
        turn_context.activity.timestamp = activity.timestamp
        turn_context.activity.text = activity.text
        turn_context.activity.type = activity.type
        turn_context.activity.value = activity.value

    async def _process_activity(
        self,
        claims_identity: ClaimsIdentity,
        conversation_id: str,
        reply_to_activity_id: Optional[str],
        activity: Activity,
    ):
        agent_conversation_reference = (
            await self._conversation_id_factory.get_agent_conversation_reference(
                conversation_id
            )
        )

        resource_response: ResourceResponse = None

        async def agent_callback_handler(turn_context: TurnContextProtocol):
            activity.apply_conversation_reference(
                agent_conversation_reference.conversation_reference
            )
            turn_context.activity.id = reply_to_activity_id
            turn_context.activity.caller_id = f"{CallerIdConstants.agent_to_agent_prefix}{claims_identity.get_outgoing_app_id()}"

            if activity.type == ActivityTypes.end_of_conversation:
                await self._conversation_id_factory.delete_conversation_reference(
                    conversation_id
                )

                Agent1._apply_activity_to_turn_context(turn_context, activity)
                await self.on_turn(turn_context)
            else:
                nonlocal resource_response
                resource_response = await turn_context.send_activity(activity)

        # TODO: fix overload
        continuation_activity = (
            agent_conversation_reference.conversation_reference.get_continuation_activity()
        )
        await self._adapter.continue_conversation_with_claims(
            claims_identity=claims_identity,
            continuation_activity=continuation_activity,
            callback=agent_callback_handler,
            audience=agent_conversation_reference.oauth_scope,
        )

        return resource_response or ResourceResponse(id=str(uuid4()))
