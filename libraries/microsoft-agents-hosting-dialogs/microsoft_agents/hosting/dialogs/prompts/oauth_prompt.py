# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import cast

from microsoft_agents.activity import (
    Channels,
    Activity,
    ActivityTypes,
    ActionTypes,
    CardAction,
    InputHints,
    SigninCard,
    SignInConstants,
    OAuthCard,
    TokenResponse,
    TokenExchangeInvokeRequest,
    TokenExchangeInvokeResponse,
    InvokeResponse,
)
from microsoft_agents.hosting.core import (
    CardFactory,
    MessageFactory,
    TurnContext,
    ChannelAdapter,
    ClaimsIdentity,
    UserTokenClient,
    MemoryStorage,
)
from microsoft_agents.hosting.core._oauth import (
    _OAuthFlow,
    _FlowStorageClient,
    _FlowState,
    _FlowStateTag,
    _FlowResponse,
)
from opentelemetry import context

from ..dialog import Dialog
from ..dialog_context import DialogContext
from ..models.dialog_turn_result import DialogTurnResult
from .prompt_options import PromptOptions
from .oauth_prompt_settings import OAuthPromptSettings

logger = logging.getLogger(__name__)


class CallerInfo:
    def __init__(self, caller_service_url: str | None = None, scope: str | None = None):
        self.caller_service_url = caller_service_url
        self.scope = scope


class OAuthPrompt(Dialog):
    PERSISTED_OPTIONS = "options"
    PERSISTED_STATE = "state"
    PERSISTED_EXPIRES = "expires"
    PERSISTED_CALLER = "caller"

    """
    Creates a new prompt that asks the user to sign in.
    """

    def __init__(
        self,
        dialog_id: str,
        settings: OAuthPromptSettings,
    ):
        super().__init__(dialog_id)
        self._storage = MemoryStorage()  # to keep track of the OAuth flow state

        if not settings:
            raise TypeError(
                "OAuthPrompt.__init__(): OAuthPrompt requires OAuthPromptSettings."
            )

        self._settings = settings

    @staticmethod
    def _get_user_token_client(context: TurnContext) -> UserTokenClient:
        return context.turn_state.get(context.adapter.USER_TOKEN_CLIENT_KEY)

    async def _load_flow(
        self, context: TurnContext
    ) -> tuple[_OAuthFlow, _FlowStorageClient]:
        """Loads the OAuth flow.

        A new flow is created in Storage if none exists for the channel, user, and handler
        combination.

        :param context: The context object for the current turn.
        :type context: TurnContext
        :return: A tuple containing the OAuthFlow and FlowStorageClient created from the
            context and the specified auth handler.
        :rtype: tuple[OAuthFlow, FlowStorageClient]
        """
        user_token_client = OAuthPrompt._get_user_token_client(context)

        if (
            not context.activity.channel_id
            or not context.activity.from_property
            or not context.activity.from_property.id
        ):
            raise ValueError("Channel ID and User ID are required")

        channel_id = context.activity.channel_id
        user_id = context.activity.from_property.id

        ms_app_id = context.turn_state.get(context.adapter.AGENT_IDENTITY_KEY).claims[
            "aud"
        ]

        # try to load existing state
        flow_storage_client = _FlowStorageClient(channel_id, user_id, self._storage)
        logger.info("Loading OAuth flow state from storage")
        flow_state: _FlowState | None = await flow_storage_client.read(self._id)
        if not flow_state:
            logger.info("No existing flow state found, creating new flow state")
            flow_state = _FlowState(
                channel_id=channel_id,
                user_id=user_id,
                auth_handler_id=self._id,
                connection=self._settings.connection_name,
                ms_app_id=ms_app_id,
            )

        timeout = (
            self._settings.timeout
            if isinstance(self._settings.timeout, int)
            else 900000
        )

        flow = _OAuthFlow(
            flow_state,
            user_token_client,
            default_flow_duration=timeout,
        )
        return flow, flow_storage_client

    async def begin_dialog(
        self, dialog_context: DialogContext, options: object = None
    ) -> DialogTurnResult:
        if dialog_context is None:
            raise TypeError(
                f"OAuthPrompt.begin_dialog(): Expected DialogContext but got NoneType instead"
            )

        prompt_options = (
            options if isinstance(options, PromptOptions) else None
        ) or PromptOptions()

        # Ensure prompts have input hint set
        if prompt_options.prompt and not prompt_options.prompt.input_hint:
            prompt_options.prompt.input_hint = InputHints.accepting_input

        if prompt_options.retry_prompt and not prompt_options.retry_prompt.input_hint:
            prompt_options.retry_prompt.input_hint = InputHints.accepting_input

        # Initialize prompt state
        timeout = (
            self._settings.timeout
            if isinstance(self._settings.timeout, int)
            else 900000
        )
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state
        state[OAuthPrompt.PERSISTED_STATE] = {}
        state[OAuthPrompt.PERSISTED_OPTIONS] = prompt_options
        state[OAuthPrompt.PERSISTED_EXPIRES] = datetime.now() + timedelta(
            seconds=timeout / 1000
        )
        state[OAuthPrompt.PERSISTED_CALLER] = OAuthPrompt.__create_caller_info(
            dialog_context.context
        )

        flow, flow_storage_client = await self._load_flow(dialog_context.context)

        flow_response: _FlowResponse = await flow.begin_flow(
            dialog_context.context.activity
        )

        await flow_storage_client.write(flow_response.flow_state)

        if flow_response.flow_state.tag == _FlowStateTag.COMPLETE:
            return await dialog_context.end_dialog(flow_response.token_response)

        await self._send_oauth_card(
            dialog_context.context, flow_response, prompt_options.prompt
        )
        return Dialog.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext) -> DialogTurnResult:
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state

        # Check for timeout
        expires = state.get(OAuthPrompt.PERSISTED_EXPIRES)
        if expires and datetime.now() > expires:
            return await dialog_context.end_dialog(None)

        flow_response = await self._continue_flow(dialog_context.context)

        if (
            flow_response is not None
            and flow_response.flow_state.tag == _FlowStateTag.COMPLETE
        ):
            return await dialog_context.end_dialog(flow_response.token_response)

        if (
            dialog_context.context.activity.type == ActivityTypes.message
            and self._settings.end_on_invalid_message
        ):
            return await dialog_context.end_dialog(None)

        if (
            not dialog_context.context.responded
            and dialog_context.context.activity.type == ActivityTypes.message
            and state[OAuthPrompt.PERSISTED_OPTIONS].retry_prompt is not None
        ):
            await dialog_context.context.send_activity(
                state[OAuthPrompt.PERSISTED_OPTIONS].retry_prompt
            )

        return Dialog.end_of_turn

    async def get_user_token(
        self, context: TurnContext, code: str = ""
    ) -> TokenResponse:
        """
        Gets the user's token.
        """
        flow, _ = await self._load_flow(context)
        return await flow.get_user_token(code)

    async def sign_out_user(self, context: TurnContext):
        """
        Signs out the user.
        """
        flow, flow_storage_client = await self._load_flow(context)
        await flow.sign_out()
        await flow_storage_client.delete(
            self._id
        )  # Clear flow state from storage after signing out

    @staticmethod
    def __create_caller_info(context: TurnContext) -> CallerInfo | None:
        bot_identity = cast(
            ClaimsIdentity | None,
            context.turn_state.get(ChannelAdapter.AGENT_IDENTITY_KEY),
        )
        if bot_identity and bot_identity.is_agent_claim():
            return CallerInfo(
                caller_service_url=context.activity.service_url,
                scope=bot_identity.get_app_id(),
            )

        return None

    async def _send_oauth_card(
        self,
        context: TurnContext,
        flow_response: _FlowResponse,
        prompt: Activity | str | None = None,
    ):
        if not isinstance(prompt, Activity):
            prompt = MessageFactory.text(prompt or "", None, InputHints.accepting_input)
        else:
            prompt.input_hint = prompt.input_hint or InputHints.accepting_input

        prompt.attachments = prompt.attachments or []

        if OAuthPrompt._channel_suppports_oauth_card(context.activity.channel_id or ""):
            if not any(
                att.content_type == CardFactory.content_types.oauth_card
                for att in prompt.attachments
            ):
                card_action_type = ActionTypes.signin
                sign_in_resource = flow_response.sign_in_resource
                link = sign_in_resource.sign_in_link
                bot_identity = cast(
                    ClaimsIdentity | None,
                    context.turn_state.get(ChannelAdapter.AGENT_IDENTITY_KEY),
                )

                # use the SignInLink when in speech channel or bot is a skill or
                # an extra OAuthAppCredentials is being passed in
                if (
                    (bot_identity and bot_identity.is_agent_claim())
                    or not context.activity.service_url.startswith("http")
                    or (
                        hasattr(self._settings, "oauth_app_credentials")
                        and self._settings.oauth_app_credentials
                    )
                ):
                    if context.activity.channel_id == Channels.emulator:
                        card_action_type = ActionTypes.open_url
                elif not OAuthPrompt._channel_requires_sign_in_link(
                    context.activity.channel_id or ""
                ):
                    link = None

                json_token_ex_resource = (
                    sign_in_resource.token_exchange_resource.model_dump()
                    if sign_in_resource.token_exchange_resource
                    else None
                )

                json_token_ex_post = (
                    sign_in_resource.token_post_resource.model_dump()
                    if hasattr(sign_in_resource, "token_post_resource")
                    and sign_in_resource.token_post_resource
                    else None
                )

                card_action_kwargs = {
                    "title": self._settings.title,
                    "type": card_action_type,
                    "value": link,
                }
                if self._settings.text:
                    card_action_kwargs["text"] = self._settings.text
                oauth_card_kwargs = {
                    "connection_name": self._settings.connection_name,
                    "buttons": [CardAction(**card_action_kwargs)],
                    "token_exchange_resource": json_token_ex_resource,
                }
                if self._settings.text:
                    oauth_card_kwargs["text"] = self._settings.text
                if json_token_ex_post:
                    oauth_card_kwargs["token_post_resource"] = json_token_ex_post
                prompt.attachments.append(
                    CardFactory.oauth_card(OAuthCard(**oauth_card_kwargs))
                )
        else:
            if not any(
                att.content_type == CardFactory.content_types.signin_card
                for att in prompt.attachments
            ):
                if not hasattr(context.adapter, "get_oauth_sign_in_link"):
                    raise Exception(
                        "OAuthPrompt._send_oauth_card(): get_oauth_sign_in_link() not supported by the current adapter"
                    )

                link = await context.adapter.get_oauth_sign_in_link(
                    context,
                    self._settings.connection_name,
                )
                prompt.attachments.append(
                    CardFactory.signin_card(
                        SigninCard(
                            text=self._settings.text or "",
                            buttons=[
                                CardAction(
                                    title=self._settings.title,
                                    value=link,
                                    type=ActionTypes.signin,
                                )
                            ],
                        )
                    )
                )

        # Send prompt
        await context.send_activity(prompt)

    @staticmethod
    def _validate_token_exchange_invoke_response(
        activity: Activity,
    ) -> TokenExchangeInvokeRequest:
        activity_value = activity.value
        if isinstance(activity_value, dict):
            activity_value = TokenExchangeInvokeRequest.model_validate(activity_value)
        return cast(TokenExchangeInvokeRequest, activity_value)

    def _validate_continue_flow(self, context: TurnContext) -> Activity | None:
        if self._is_token_exchange_request_invoke(context):
            activity_value = context.activity.value
            if isinstance(activity_value, dict):
                activity_value = TokenExchangeInvokeRequest.model_validate(
                    activity_value
                )

            token_exchange_invoke_request = (
                OAuthPrompt._validate_token_exchange_invoke_response(context.activity)
            )

            if not (
                token_exchange_invoke_request
                and self._is_token_exchange_request(token_exchange_invoke_request)
            ):
                # Received activity is not a token exchange request.
                return self._get_token_exchange_invoke_response(
                    int(HTTPStatus.BAD_REQUEST),
                    "The bot received an InvokeActivity that is missing a TokenExchangeInvokeRequest value."
                    " This is required to be sent with the InvokeActivity.",
                )
            elif (
                token_exchange_invoke_request.connection_name
                != self._settings.connection_name
            ):
                # Connection name on activity does not match that of setting.
                return self._get_token_exchange_invoke_response(
                    int(HTTPStatus.BAD_REQUEST),
                    "The bot received an InvokeActivity with a TokenExchangeInvokeRequest containing a"
                    " ConnectionName that does not match the ConnectionName expected by the bots active"
                    " OAuthPrompt. Ensure these names match when sending the InvokeActivity.",
                )

    async def _exchange_token(
        self, context: TurnContext, input_token_response: TokenResponse | None
    ) -> TokenResponse | None:
        if not input_token_response:
            return input_token_response

        user_id = context.activity.from_property.id
        channel_id = (
            context.activity.channel_id.channel if context.activity.channel_id else ""
        )

        user_token_client = OAuthPrompt._get_user_token_client(context)

        return await user_token_client.user_token.exchange_token(
            user_id,
            self._settings.connection_name,
            channel_id,
            {"token": input_token_response.token},
        )

    async def _continue_flow(
        self,
        context: TurnContext,
    ) -> _FlowResponse | None:

        flow_response: _FlowResponse | None = None

        error_response = self._validate_continue_flow(context)
        if error_response:
            await context.send_activity(error_response)

        # do something here

        flow, flow_storage_client = await self._load_flow(context)

        if error_response is None:

            try:
                flow_response = await flow.continue_flow(context.activity)
            except Exception:
                error_response = Activity(  # type: ignore[call-arg]
                    type=ActivityTypes.invoke_response,
                    value=InvokeResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR),
                )

            if error_response is None:
                assert flow_response is not None
                await flow_storage_client.write(flow.flow_state)

                token_response: TokenResponse | None = flow_response.token_response

                if OAuthPrompt._is_teams_verification_invoke(context):
                    if token_response:
                        await context.send_activity(
                            Activity(  # type: ignore[call-arg]
                                type=ActivityTypes.invoke_response,
                                value=InvokeResponse(status=HTTPStatus.OK),
                            )
                        )
                    else:
                        await context.send_activity(
                            Activity(  # type: ignore[call-arg]
                                type=ActivityTypes.invoke_response,
                                value=InvokeResponse(status=HTTPStatus.NOT_FOUND),
                            )
                        )
                elif self._is_token_exchange_request_invoke(context):

                    token_exchange_response: TokenResponse | None = None

                    token_exchange_response = await self._exchange_token(
                        context, token_response
                    )

                    if token_exchange_response:
                        await context.send_activity(
                            self._get_token_exchange_invoke_response(
                                int(HTTPStatus.OK), None
                            )
                        )
                    else:
                        await context.send_activity(
                            self._get_token_exchange_invoke_response(
                                int(HTTPStatus.PRECONDITION_FAILED),
                                "The bot is unable to exchange token. Proceed with regular login.",
                            )
                        )

        return flow_response

    def _get_token_exchange_invoke_response(
        self, status: int, failure_detail: str | None, identifier: str | None = None
    ) -> Activity:
        return Activity(  # type: ignore[call-arg]
            type=ActivityTypes.invoke_response,
            value=InvokeResponse(
                status=status,
                body=TokenExchangeInvokeResponse(
                    id=identifier,  # type: ignore[arg-type]
                    connection_name=self._settings.connection_name,
                    failure_detail=failure_detail,  # type: ignore[arg-type]
                ),
            ),
        )

    @staticmethod
    def _is_token_response_event(context: TurnContext) -> bool:
        activity = context.activity

        return (
            activity.type == ActivityTypes.event
            and activity.name == SignInConstants.token_response_event_name
        )

    @staticmethod
    def _is_teams_verification_invoke(context: TurnContext) -> bool:
        activity = context.activity

        return (
            activity.type == ActivityTypes.invoke
            and activity.name == SignInConstants.verify_state_operation_name
        )

    @staticmethod
    def _channel_suppports_oauth_card(channel_id: str) -> bool:
        if channel_id in [
            Channels.cortana,
            Channels.skype,
            Channels.skype_for_business,
        ]:
            return False

        return True

    @staticmethod
    def _channel_requires_sign_in_link(channel_id: str) -> bool:
        if channel_id in [Channels.ms_teams]:
            return True

        return False

    @staticmethod
    def _is_token_exchange_request_invoke(context: TurnContext) -> bool:
        activity = context.activity

        return (
            activity.type == ActivityTypes.invoke
            and activity.name == SignInConstants.token_exchange_operation_name
        )

    @staticmethod
    def _is_token_exchange_request(obj: TokenExchangeInvokeRequest) -> bool:
        return bool(obj.connection_name) and bool(obj.token)
