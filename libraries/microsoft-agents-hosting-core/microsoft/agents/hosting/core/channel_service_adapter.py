# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from asyncio import sleep
from abc import ABC
from copy import Error
from http import HTTPStatus
from typing import Awaitable, Callable, cast
from uuid import uuid4

from microsoft.agents.activity import (
    Activity,
    ActivityEventNames,
    ActivityTypes,
    CallerIdConstants,
    Channels,
    ConversationAccount,
    ConversationReference,
    ConversationResourceResponse,
    ConversationParameters,
    DeliveryModes,
    ExpectedReplies,
    InvokeResponse,
    ResourceResponse,
)
from microsoft.agents.hosting.core.connector import (
    ConnectorClientBase,
    UserTokenClientBase,
    ConnectorClient,
    UserTokenClient,
)
from microsoft.agents.hosting.core.authorization import (
    AuthenticationConstants,
    ClaimsIdentity,
)
from .channel_service_client_factory_base import ChannelServiceClientFactoryBase
from .channel_adapter import ChannelAdapter
from .turn_context import TurnContext


class ChannelServiceAdapter(ChannelAdapter, ABC):
    _AGENT_CONNECTOR_CLIENT_KEY = "ConnectorClient"

    def __init__(self, channel_service_client_factory: ChannelServiceClientFactoryBase):
        super().__init__()
        self._channel_service_client_factory = channel_service_client_factory

    async def send_activities(
        self, context: TurnContext, activities: list[Activity]
    ) -> list[ResourceResponse]:
        if not context:
            raise TypeError("Expected TurnContext but got None instead")

        if activities is None:
            raise TypeError("Expected Activities list but got None instead")

        if len(activities) == 0:
            raise TypeError("Expecting one or more activities, but the list was empty.")

        responses = []

        for activity in activities:
            activity.id = None

            response = ResourceResponse()

            if activity.type == "delay":
                delay_time = int((activity.value or 1000) / 1000)
                await sleep(delay_time)
            elif activity.type == ActivityTypes.invoke_response:
                context.turn_state[self.INVOKE_RESPONSE_KEY] = activity
            elif (
                activity.type == ActivityTypes.trace
                and activity.channel_id != Channels.emulator
            ):
                # no-op
                pass
            else:
                connector_client = cast(
                    ConnectorClientBase,
                    context.turn_state.get(self._AGENT_CONNECTOR_CLIENT_KEY),
                )
                if not connector_client:
                    raise Error("Unable to extract ConnectorClient from turn context.")

                if activity.reply_to_id:
                    response = await connector_client.conversations.reply_to_activity(
                        activity.conversation.id,
                        activity.reply_to_id,
                        activity,
                    )
                else:
                    response = (
                        await connector_client.conversations.send_to_conversation(
                            activity.conversation.id,
                            activity,
                        )
                    )
            response = response or ResourceResponse(id=activity.id or "")

            responses.append(response)

        return responses

    async def update_activity(self, context: TurnContext, activity: Activity):
        if not context:
            raise TypeError("Expected TurnContext but got None instead")

        if activity is None:
            raise TypeError("Expected Activity but got None instead")

        connector_client = cast(
            ConnectorClientBase,
            context.turn_state.get(self._AGENT_CONNECTOR_CLIENT_KEY),
        )
        if not connector_client:
            raise Error("Unable to extract ConnectorClient from turn context.")

        return await connector_client.conversations.update_activity(
            activity.conversation.id, activity.id, activity
        )

    async def delete_activity(
        self, context: TurnContext, reference: ConversationReference
    ):
        if not context:
            raise TypeError("Expected TurnContext but got None instead")

        if not reference:
            raise TypeError("Expected ConversationReference but got None instead")

        connector_client = cast(
            ConnectorClientBase,
            context.turn_state.get(self._AGENT_CONNECTOR_CLIENT_KEY),
        )
        if not connector_client:
            raise Error("Unable to extract ConnectorClient from turn context.")

        await connector_client.conversations.delete_activity(
            reference.conversation.id, reference.activity_id
        )

    async def continue_conversation(  # pylint: disable=arguments-differ
        self,
        agent_app_id: str,
        continuation_activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
    ):
        """
        Sends a proactive message to a conversation.
        Call this method to proactively send a message to a conversation.
        Most channels require a user to initiate a conversation with an agent before the agent can send activities
        to the user.

        :param reference: A reference to the conversation to continue.
        :type reference: :class:`hosting.schema.ConversationReference`
        :param callback: The method to call for the resulting agent turn.
        :type callback: :class:`typing.Callable`
        :param agent_app_id: The application Id of the agent. This is the appId returned by the Azure portal registration,
        and is generally found in the `MicrosoftAppId` parameter in `config.py`.
        :type agent_app_id: :class:`typing.str`
        """
        if not callable:
            raise TypeError(
                "Expected Callback (Callable[[TurnContext], Awaitable]) but got None instead"
            )

        self._validate_continuation_activity(continuation_activity)

        claims_identity = self.create_claims_identity(agent_app_id)

        return await self.process_proactive(
            claims_identity,
            continuation_activity,
            claims_identity.get_token_audience(),
            callback,
        )

    async def continue_conversation_with_claims(
        self,
        claims_identity: ClaimsIdentity,
        continuation_activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
        audience: str = None,
    ):
        return await self.process_proactive(
            claims_identity, continuation_activity, audience, callback
        )

    async def create_conversation(  # pylint: disable=arguments-differ
        self,
        agent_app_id: str,
        channel_id: str,
        service_url: str,
        audience: str,
        conversation_parameters: ConversationParameters,
        callback: Callable[[TurnContext], Awaitable],
    ):
        if not service_url:
            raise TypeError(
                "CloudAdapter.create_conversation(): service_url is required."
            )
        if not conversation_parameters:
            raise TypeError(
                "CloudAdapter.create_conversation(): conversation_parameters is required."
            )
        if not callback:
            raise TypeError("CloudAdapter.create_conversation(): callback is required.")

        # Create a ClaimsIdentity, to create the connector and for adding to the turn context.
        claims_identity = self.create_claims_identity(agent_app_id)
        claims_identity.claims[AuthenticationConstants.SERVICE_URL_CLAIM] = service_url

        # Create the connector client to use for outbound requests.
        connector_client: ConnectorClient = (
            await self._channel_service_client_factory.create_connector_client(
                claims_identity, service_url, audience
            )
        )

        # Make the actual create conversation call using the connector.
        create_conversation_result = (
            await connector_client.conversations.create_conversation(
                conversation_parameters
            )
        )

        # Create the create activity to communicate the results to the application.
        create_activity = self._create_create_activity(
            create_conversation_result, channel_id, service_url, conversation_parameters
        )

        # Create a UserTokenClient instance for the application to use. (For example, in the OAuthPrompt.)
        user_token_client: UserTokenClient = (
            await self._channel_service_client_factory.create_user_token_client(
                claims_identity
            )
        )

        # Create a turn context and run the pipeline.
        context = self._create_turn_context(
            create_activity,
            claims_identity,
            None,
            connector_client,
            user_token_client,
            callback,
        )

        # Run the pipeline
        await self.run_pipeline(context, callback)

        await connector_client.close()
        await user_token_client.close()

    async def process_proactive(
        self,
        claims_identity: ClaimsIdentity,
        continuation_activity: Activity,
        audience: str,
        callback: Callable[[TurnContext], Awaitable],
    ):
        # Create the connector client to use for outbound requests.
        connector_client: ConnectorClient = (
            await self._channel_service_client_factory.create_connector_client(
                claims_identity, continuation_activity.service_url, audience
            )
        )

        # Create a UserTokenClient instance for the application to use. (For example, in the OAuthPrompt.)
        user_token_client: UserTokenClient = (
            await self._channel_service_client_factory.create_user_token_client(
                claims_identity
            )
        )

        # Create a turn context and run the pipeline.
        context = self._create_turn_context(
            continuation_activity,
            claims_identity,
            audience,
            connector_client,
            user_token_client,
            callback,
        )

        # Run the pipeline
        await self.run_pipeline(context, callback)

        await connector_client.close()
        await user_token_client.close()

    async def process_activity(
        self,
        claims_identity: ClaimsIdentity,
        activity: Activity,
        callback: Callable[[TurnContext], Awaitable],
    ):
        """
        Creates a turn context and runs the middleware pipeline for an incoming activity.

        :param auth_header: The HTTP authentication header of the request
        :type auth_header: :class:`typing.Union[typing.str, AuthenticateRequestResult]`
        :param activity: The incoming activity
        :type activity: :class:`Activity`
        :param callback: The callback to execute at the end of the adapter's middleware pipeline.
        :type callback: :class:`typing.Callable`

        :return: A task that represents the work queued to execute.

        .. remarks::
            This class processes an activity received by the agents web server. This includes any messages
            sent from a user and is the method that drives what's often referred to as the
            agent *reactive messaging* flow.
            Call this method to reactively send a message to a conversation.
            If the task completes successfully, then an :class:`InvokeResponse` is returned;
            otherwise. `null` is returned.
        """
        scopes: list[str] = None
        outgoing_audience: str = None

        if claims_identity.is_agent_claim():
            outgoing_audience = claims_identity.get_token_audience()
            scopes = [f"{claims_identity.get_outgoing_app_id()}/.default"]
            activity.caller_id = f"{CallerIdConstants.agent_to_agent_prefix}{claims_identity.get_outgoing_app_id()}"
        else:
            outgoing_audience = AuthenticationConstants.AGENTS_SDK_SCOPE
            scopes = [f"{AuthenticationConstants.AGENTS_SDK_SCOPE}/.default"]

        use_anonymous_auth_callback = False
        if (
            not claims_identity.is_authenticated
            and claims_identity.authentication_type == "Anonymous"
        ):
            use_anonymous_auth_callback = True

        # Create the connector client to use for outbound requests.
        connector_client: ConnectorClient = (
            await self._channel_service_client_factory.create_connector_client(
                claims_identity,
                activity.service_url,
                outgoing_audience,
                scopes,
                use_anonymous_auth_callback,
            )
        )

        # Create a UserTokenClient instance for the OAuth flow.
        user_token_client: UserTokenClient = (
            await self._channel_service_client_factory.create_user_token_client(
                claims_identity, use_anonymous_auth_callback
            )
        )

        # Create a turn context and run the pipeline.
        context = self._create_turn_context(
            activity,
            claims_identity,
            outgoing_audience,
            connector_client,
            user_token_client,
            callback,
        )

        await self.run_pipeline(context, callback)

        await connector_client.close()
        await user_token_client.close()

        # If there are any results they will have been left on the TurnContext.
        return self._process_turn_results(context)

    def create_claims_identity(self, agent_app_id: str = "") -> ClaimsIdentity:
        return ClaimsIdentity(
            {
                AuthenticationConstants.AUDIENCE_CLAIM: agent_app_id,
                AuthenticationConstants.APP_ID_CLAIM: agent_app_id,
            },
            False,
        )

    @staticmethod
    def _validate_continuation_activity(continuation_activity: Activity):
        if not continuation_activity:
            raise TypeError("CloudAdapter: continuation_activity is required.")

        if not continuation_activity.conversation:
            raise TypeError(
                "CloudAdapter: continuation_activity.conversation is required."
            )

        if not continuation_activity.service_url:
            raise TypeError(
                "CloudAdapter: continuation_activity.service_url is required."
            )

    def _create_create_activity(
        self,
        create_conversation_result: ConversationResourceResponse,
        channel_id: str,
        service_url: str,
        conversation_parameters: ConversationParameters,
    ) -> Activity:
        # Create a conversation update activity to represent the result.
        activity = Activity.create_event_activity()
        activity.name = ActivityEventNames.create_conversation
        activity.channel_id = channel_id
        activity.service_url = service_url
        activity.id = create_conversation_result.activity_id or str(uuid4())
        activity.conversation = ConversationAccount(
            id=create_conversation_result.id,
            tenant_id=conversation_parameters.tenant_id,
        )
        activity.channel_data = conversation_parameters.channel_data
        activity.recipient = conversation_parameters.agent

        return activity

    def _create_turn_context(
        self,
        activity: Activity,
        claims_identity: ClaimsIdentity,
        oauth_scope: str,
        connector_client: ConnectorClientBase,
        user_token_client: UserTokenClientBase,
        callback: Callable[[TurnContext], Awaitable],
    ) -> TurnContext:
        context = TurnContext(self, activity)

        context.turn_state[self.AGENT_IDENTITY_KEY] = claims_identity
        context.turn_state[self._AGENT_CONNECTOR_CLIENT_KEY] = connector_client
        context.turn_state[self.USER_TOKEN_CLIENT_KEY] = user_token_client
        context.turn_state[self.AGENT_CALLBACK_HANDLER_KEY] = callback
        context.turn_state[self.CHANNEL_SERVICE_FACTORY_KEY] = (
            self._channel_service_client_factory
        )
        context.turn_state[self.OAUTH_SCOPE_KEY] = oauth_scope

        return context

    def _process_turn_results(self, context: TurnContext) -> InvokeResponse:
        # Handle ExpectedReplies scenarios where all activities have been
        # buffered and sent back at once in an invoke response.
        if context.activity.delivery_mode == DeliveryModes.expect_replies:
            return InvokeResponse(
                status=HTTPStatus.OK,
                body=ExpectedReplies(
                    activities=context.buffered_reply_activities
                ).model_dump(mode="json", by_alias=True, exclude_unset=True),
            )

        # Handle Invoke scenarios where the agent will return a specific body and return code.
        if context.activity.type == ActivityTypes.invoke:
            activity_invoke_response: Activity = context.turn_state.get(
                self.INVOKE_RESPONSE_KEY
            )
            if not activity_invoke_response:
                return InvokeResponse(status=HTTPStatus.NOT_IMPLEMENTED)

            return InvokeResponse.model_validate(activity_invoke_response.value)

        # No body to return
        return None
