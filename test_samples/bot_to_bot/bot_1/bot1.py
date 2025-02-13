from typing import Any

from aiohttp.web import HTTPException

from microsoft.agents.core import ChannelAdapterProtocol, TurnContextProtocol
from microsoft.agents.core.models import (
    ActivityTypes,
    Activity,
    CallerIdConstants,
    ChannelAccount,
    ResourceResponse,
)
from microsoft.agents.authentication import BotClaims, ClaimsIdentity
from microsoft.agents.client import (
    ChannelHostProtocol,
    ChannelInfoProtocol,
    ConversationIdFactoryProtocol,
    ConversationIdFactoryOptions,
)
from microsoft.agents.botbuilder import (
    ActivityHandler,
    ChannelApiHandlerProtocol,
    ChannelAdapter,
)


class Bot1(ActivityHandler, ChannelApiHandlerProtocol):
    ACTIVE_SKILL_PROPERTY_NAME = "Bot1.ActiveSkillProperty"
    _active_bot_client = False

    def __init__(
        self,
        adapter: ChannelAdapterProtocol,
        channel_host: ChannelHostProtocol,
        conversation_id_factory: ConversationIdFactoryProtocol,
    ):
        if not adapter:
            raise ValueError("Bot1.__init__(): adapter cannot be None")
        if not channel_host:
            raise ValueError("Bot1.__init__(): channel_host cannot be None")
        if not conversation_id_factory:
            raise ValueError("Bot1.__init__(): conversation_id_factory cannot be None")

        self._adapter = adapter
        self._channel_host = channel_host
        self._conversation_id_factory = conversation_id_factory

        target_skill_id = "EchoSkillBot"
        self._target_skill = self._channel_host.channels.get(target_skill_id)

    async def on_turn(self, turn_context: TurnContextProtocol):
        # Forward all activities except EndOfConversation to the skill
        if turn_context.activity.type == ActivityTypes.end_of_conversation:
            # Try to get the active skill
            if Bot1._active_bot_client:
                # await Bot1._active_bot_client.on_turn(turn_context)
                return

        await super().on_turn(turn_context)

    # update when doing activity type protocols
    async def on_message_activity(self, turn_context: TurnContextProtocol):
        if "agent" in turn_context.activity.text.lower():
            # TODO: review activity | str interface for send_activity
            await turn_context.send_activity("Got it, connecting you to the agent...")

            Bot1._active_bot_client = True

            # send to bot
            return

        await turn_context.send_activity('Say "agent" and I\'ll patch you through')

    async def on_end_of_conversation_activity(self, turn_context: TurnContextProtocol):
        # Clear the active skill
        Bot1._active_bot_client = False

        # Show status message, text and value returned by the skill
        eoc_activity_message = f"Received {turn_context.activity.type}. Code: {turn_context.activity.code}."
        if turn_context.activity.text:
            eoc_activity_message += f" Text: {turn_context.activity.text}"

        if turn_context.activity.value:
            eoc_activity_message += f" Value: {turn_context.activity.value}"

        await turn_context.send_activity(eoc_activity_message)
        await turn_context.send_activity(
            'Back in the root bot. Say "agent" and I\'ll patch you through'
        )

    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContextProtocol
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    'Hello and welcome! Say "agent" and I\'ll patch you through'
                )

    async def _send_to_bot(
        self, turn_context: TurnContextProtocol, target_channel: ChannelInfoProtocol
    ):
        # Create a conversation ID to communicate with the skill
        options = ConversationIdFactoryOptions(
            from_oauth_scope=turn_context.turn_state.get(
                ChannelAdapter.OAUTH_SCOPE_KEY
            ),
            from_bot_id=self._channel_host.host_app_id,
            activity=turn_context.activity,
            bot=target_channel,
        )

        conversation_id = await self._conversation_id_factory.create_conversation_id(
            options
        )

        # TODO: might need to close connection, tbd
        channel = self._channel_host.get_channel(target_channel)

        # Route activity to the skill
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
                f'Error invoking the id: "{target_channel.id}" at "{target_channel.endpoint}" (status is {response.status}). \r\n {response.body}'
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
        reply_to_activity_id: str,
        activity: Activity,
    ):
        bot_conversation_reference = (
            await self._conversation_id_factory.get_conversation_reference(
                conversation_id
            )
        )

        resource_response: ResourceResponse = None

        async def bot_callback_handler(turn_context: TurnContextProtocol):
            activity.apply_conversation_reference(
                bot_conversation_reference.conversation_reference
            )
            turn_context.activity.id = reply_to_activity_id
            turn_context.activity.caller_id = f"{CallerIdConstants.bot_to_bot_prefix}{claims_identity.get_outgoing_app_id()}"

            if activity.type == ActivityTypes.end_of_conversation:
                await self._conversation_id_factory.delete_conversation_reference(
                    conversation_id
                )

                Bot1._apply_activity_to_turn_context(turn_context, activity)
                await self.on_turn(turn_context)
            else:
                resource_response = await turn_context.send_activity(activity)

        # TODO: fix overload
        await self._adapter.continue_conversation(
            activity, claims_identity, bot_callback_handler
        )
