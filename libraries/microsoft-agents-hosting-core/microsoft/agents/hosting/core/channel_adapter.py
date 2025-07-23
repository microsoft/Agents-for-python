# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import List, Awaitable
from microsoft.agents.hosting.core.authorization import ClaimsIdentity
from microsoft.agents.activity import ChannelAdapterProtocol
from microsoft.agents.activity import (
    Activity,
    ConversationAccount,
    ConversationReference,
    ConversationParameters,
    ResourceResponse,
)

from .turn_context import TurnContext
from .middleware_set import MiddlewareSet


class ChannelAdapter(ABC, ChannelAdapterProtocol):
    AGENT_IDENTITY_KEY = "AgentIdentity"
    OAUTH_SCOPE_KEY = "Microsoft.Agents.Builder.ChannelAdapter.OAuthScope"
    INVOKE_RESPONSE_KEY = "ChannelAdapter.InvokeResponse"
    CONNECTOR_FACTORY_KEY = "ConnectorFactory"
    USER_TOKEN_CLIENT_KEY = "UserTokenClient"
    AGENT_CALLBACK_HANDLER_KEY = "AgentCallbackHandler"
    CHANNEL_SERVICE_FACTORY_KEY = "ChannelServiceClientFactory"

    on_turn_error: Callable[[TurnContext, Exception], Awaitable] = None

    def __init__(self):
        self.middleware_set = MiddlewareSet()

    @abstractmethod
    async def send_activities(
        self, context: TurnContext, activities: List[Activity]
    ) -> List[ResourceResponse]:
        """
        Sends a set of activities to the user. An array of responses from the server will be returned.

        :param context: The context object for the turn.
        :type context: :class:`TurnContext`
        :param activities: The activities to send.
        :type activities: :class:`typing.List[Activity]`
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def update_activity(self, context: TurnContext, activity: Activity):
        """
        Replaces an existing activity.

        :param context: The context object for the turn.
        :type context: :class:`TurnContext`
        :param activity: New replacement activity.
        :type activity: :class:`hosting.schema.Activity`
        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    async def delete_activity(
        self, context: TurnContext, reference: ConversationReference
    ):
        """
        Deletes an existing activity.

        :param context: The context object for the turn.
        :type context: :class:`TurnContext`
        :param reference: Conversation reference for the activity to delete.
        :type reference: :class:`hosting.schema.ConversationReference`
        :return:
        """
        raise NotImplementedError()

    def use(self, middleware):
        """
        Registers a middleware handler with the adapter.

        :param middleware: The middleware to register.
        :return:
        """
        self.middleware_set.use(middleware)
        return self

    async def continue_conversation(
        self,
        agent_id: str,  # pylint: disable=unused-argument
        reference: ConversationReference,
        callback: Callable[[TurnContext], Awaitable],
    ):
        """
        Sends a proactive message to a conversation. Call this method to proactively send a message to a conversation.
        Most channels require a user to initiate a conversation with an agent before the agent can send activities
        to the user.

        :param agent_id: The application ID of the agent. This parameter is ignored in
        single tenant the Adapters (Console, Test, etc) but is critical to the ChannelAdapter
        which is multi-tenant aware.
        :param reference: A reference to the conversation to continue.
        :type reference: :class:`hosting.schema.ConversationReference`
        :param callback: The method to call for the resulting agent turn.
        :type callback: :class:`typing.Callable`
        :param claims_identity: A :class:`microsoft.agents.authentication.ClaimsIdentity` for the conversation.
        :type claims_identity: :class:`microsoft.agents.authentication.ClaimsIdentity`
        :param audience:A value signifying the recipient of the proactive message.
        :type audience: str
        """
        context = TurnContext(self, reference.get_continuation_activity())
        return await self.run_pipeline(context, callback)

    async def continue_conversation_with_claims(
        self,
        claims_identity: ClaimsIdentity,
        continuation_activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
        audience: str = None,
    ):
        """
        Sends a proactive message to a conversation. Call this method to proactively send a message to a conversation.
        Most channels require a user to initiate a conversation with an agent before the agent can send activities
        to the user.

        :param claims_identity: A :class:`microsoft.agents.authentication.ClaimsIdentity` for the conversation.
        :type claims_identity: :class:`microsoft.agents.authentication.ClaimsIdentity`
        :param continuation_activity: The activity to send.
        :type continuation_activity: :class:`hosting
        :param callback: The method to call for the resulting agent turn.
        :type callback: :class:`typing.Callable`
        :param audience: A value signifying the recipient of the proactive message.
        :type audience: str
        """
        raise NotImplementedError()

    async def create_conversation(
        self,
        agent_app_id: str,
        channel_id: str,
        service_url: str,
        audience: str,
        conversation_parameters: ConversationParameters,
        callback: Callable[[TurnContext], Awaitable],
    ):
        """
        Starts a new conversation with a user. Used to direct message to a member of a group.

        :param agent_app_id: The application ID of the agent.
        :type agent_app_id: str
        :param channel_id: The ID for the channel.
        :type channel_id: str
        :param service_url: The channel's service URL endpoint.
        :type service_url: str
        :param audience: A value signifying the recipient of the proactive message.
        :type audience: str
        :param conversation_parameters: The information to use to create the conversation
        :type conversation_parameters: :class:`microsoft.agents.activity.models.ConversationParameters`
        :param callback: The method to call for the resulting agent turn.
        :type callback: :class:`typing.Callable[[TurnContext], Awaitable]`

        :raises: Exception - Not implemented or when the implementation fails.

        :return: A task representing the work queued to execute.

        .. remarks::
            To start a conversation, your agent must know its account information and the user's
            account information on that channel.
            Most channels only support initiating a direct message (non-group) conversation.
            The adapter attempts to create a new conversation on the channel, and
            then sends a conversation update activity through its middleware pipeline
            to the the callback method.
            If the conversation is established with the specified users, the ID of the activity
            will contain the ID of the new conversation.
        """
        from microsoft.agents.activity import ActivityTypes

        # If credentials are not provided, we can't create a conversation
        if not conversation_parameters:
            raise Exception("conversation_parameters is required")

        if (
            not conversation_parameters.members
            or len(conversation_parameters.members) == 0
        ):
            raise Exception("Conversation parameters must include at least one member")

        # Create a new conversation account if none is provided
        if (
            not conversation_parameters.conversation
            or not conversation_parameters.conversation.id
        ):
            from uuid import uuid4

            conversation_parameters.conversation = ConversationAccount(id=str(uuid4()))

        # Create a conversation update activity
        conversation_update = Activity(
            type=ActivityTypes.CONVERSATION_UPDATE,
            channel_id=channel_id,
            service_url=service_url,
            conversation=conversation_parameters.conversation,
            recipient=conversation_parameters.bot,
            from_property=conversation_parameters.members[0],
            members_added=conversation_parameters.members,
        )

        # Create a context for the activity
        context = TurnContext(self, conversation_update)

        # Set conversation parameters in context data bag
        context.turn_state["ConversationParameters"] = conversation_parameters

        # Process the activity through the middleware pipeline
        return await self.run_pipeline(context, callback)

    async def run_pipeline(
        self, context: TurnContext, callback: Callable[[TurnContext], Awaitable] = None
    ):
        """
        Called by the parent class to run the adapters middleware set and calls the passed in `callback()` handler at
        the end of the chain.

        :param context: The context object for the turn.
        :type context: :class:`TurnContext`
        :param callback: A callback method to run at the end of the pipeline.
        :type callback: :class:`typing.Callable[[TurnContext], Awaitable]`
        :return:
        """
        if context is None:
            raise TypeError(context.__class__.__name__)

        if context.activity is not None:
            try:
                return await self.middleware_set.receive_activity_with_status(
                    context, callback
                )
            except Exception as error:
                if self.on_turn_error is not None:
                    await self.on_turn_error(context, error)
                else:
                    raise error
        else:
            # callback to caller on proactive case
            if callback is not None:
                await callback(context)
