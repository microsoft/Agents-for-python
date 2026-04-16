# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import re
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Awaitable, Callable, cast

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
)

from ..dialog import Dialog
from ..dialog_context import DialogContext
from ..models.dialog_turn_result import DialogTurnResult
from .prompt_options import PromptOptions
from .oauth_prompt_settings import OAuthPromptSettings
from .prompt_validator_context import PromptValidatorContext
from .prompt_recognizer_result import PromptRecognizerResult
from .._user_token_access import _UserTokenAccess


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
    Creates a new prompt that asks the user to sign in, using the Bot Framework Single Sign On (SSO) service.
    """

    def __init__(
        self,
        dialog_id: str,
        settings: OAuthPromptSettings,
        validator: Callable[[PromptValidatorContext], Awaitable[bool]] | None = None,
    ):
        super().__init__(dialog_id)
        self._validator = validator

        if not settings:
            raise TypeError(
                "OAuthPrompt.__init__(): OAuthPrompt requires OAuthPromptSettings."
            )

        self._settings = settings
        self._validator = validator

    async def begin_dialog(
        self, dialog_context: DialogContext, options: object = None
    ) -> DialogTurnResult:
        if dialog_context is None:
            raise TypeError(
                f"OAuthPrompt.begin_dialog(): Expected DialogContext but got NoneType instead"
            )

        prompt_options = (options if isinstance(options, PromptOptions) else None) or PromptOptions()

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

        output = await _UserTokenAccess.get_user_token(
            dialog_context.context, self._settings, None
        )

        if output is not None:
            # Return token
            return await dialog_context.end_dialog(output)

        await self._send_oauth_card(dialog_context.context, prompt_options.prompt)
        return Dialog.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext) -> DialogTurnResult:
        # Check for timeout
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state
        is_message = dialog_context.context.activity.type == ActivityTypes.message
        is_timeout_activity_type = (
            is_message
            or OAuthPrompt._is_token_response_event(dialog_context.context)
            or OAuthPrompt._is_teams_verification_invoke(dialog_context.context)
            or OAuthPrompt._is_token_exchange_request_invoke(dialog_context.context)
        )

        has_timed_out = is_timeout_activity_type and (
            datetime.now() > state[OAuthPrompt.PERSISTED_EXPIRES]
        )

        if has_timed_out:
            return await dialog_context.end_dialog(None)

        if state["state"].get("attemptCount") is None:
            state["state"]["attemptCount"] = 1
        else:
            state["state"]["attemptCount"] += 1

        # Recognize token
        recognized = await self._recognize_token(dialog_context)

        # Validate the return value
        is_valid = False
        if self._validator is not None:
            is_valid = await self._validator(
                PromptValidatorContext(
                    dialog_context.context,
                    recognized,
                    state[OAuthPrompt.PERSISTED_STATE],
                    state[OAuthPrompt.PERSISTED_OPTIONS],
                )
            )
        elif recognized.succeeded:
            is_valid = True

        # Return recognized value or re-prompt
        if is_valid:
            return await dialog_context.end_dialog(recognized.value)
        if is_message and self._settings.end_on_invalid_message:
            # If EndOnInvalidMessage is set, complete the prompt with no result.
            return await dialog_context.end_dialog(None)

        # Send retry prompt
        if (
            not dialog_context.context.responded
            and is_message
            and state[OAuthPrompt.PERSISTED_OPTIONS].retry_prompt is not None
        ):
            await dialog_context.context.send_activity(
                state[OAuthPrompt.PERSISTED_OPTIONS].retry_prompt
            )

        return Dialog.end_of_turn

    async def get_user_token(
        self, context: TurnContext, code: str | None = None
    ) -> TokenResponse:
        """
        Gets the user's token.
        """
        return await _UserTokenAccess.get_user_token(context, self._settings, code)

    async def sign_out_user(self, context: TurnContext):
        """
        Signs out the user.
        """
        return await _UserTokenAccess.sign_out_user(context, self._settings)

    @staticmethod
    def __create_caller_info(context: TurnContext) -> CallerInfo | None:
        bot_identity = cast(ClaimsIdentity | None, context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY
        ))
        if bot_identity and bot_identity.is_agent_claim():
            return CallerInfo(
                caller_service_url=context.activity.service_url,
                scope=bot_identity.get_app_id(),
            )

        return None

    async def _send_oauth_card(
        self, context: TurnContext, prompt: Activity | str | None = None
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
                sign_in_resource = await _UserTokenAccess.get_sign_in_resource(
                    context, self._settings
                )
                link = sign_in_resource.sign_in_link
                bot_identity = cast(ClaimsIdentity | None, context.turn_state.get(
                    ChannelAdapter.AGENT_IDENTITY_KEY
                ))

                # use the SignInLink when in speech channel or bot is a skill or
                # an extra OAuthAppCredentials is being passed in
                if (
                    (bot_identity and bot_identity.is_agent_claim())
                    or not context.activity.service_url.startswith("http")
                    or (
                        hasattr(self._settings, "oath_app_credentials")
                        and self._settings.oath_app_credentials
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

    async def _recognize_token(
        self, dialog_context: DialogContext
    ) -> PromptRecognizerResult:
        context = dialog_context.context
        token = None
        if OAuthPrompt._is_token_response_event(context):
            token = context.activity.value

        elif OAuthPrompt._is_teams_verification_invoke(context):
            code = (
                cast(dict, context.activity.value).get("state", None)
                if isinstance(context.activity.value, dict)
                else None
            )
            try:
                token = await _UserTokenAccess.get_user_token(
                    context, self._settings, code
                )
                if token is not None:
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
            except Exception:
                await context.send_activity(
                    Activity(  # type: ignore[call-arg]
                        type=ActivityTypes.invoke_response,
                        value=InvokeResponse(status=HTTPStatus.INTERNAL_SERVER_ERROR),
                    )
                )
        elif self._is_token_exchange_request_invoke(context):
            if isinstance(context.activity.value, dict):
                context.activity.value = TokenExchangeInvokeRequest.model_validate(
                    context.activity.value
                )

            token_value = cast(TokenExchangeInvokeRequest, context.activity.value)

            if not (
                token_value
                and self._is_token_exchange_request(token_value)
            ):
                # Received activity is not a token exchange request.
                await context.send_activity(
                    self._get_token_exchange_invoke_response(
                        int(HTTPStatus.BAD_REQUEST),
                        "The bot received an InvokeActivity that is missing a TokenExchangeInvokeRequest value."
                        " This is required to be sent with the InvokeActivity.",
                    )
                )
            elif (
                token_value.connection_name != self._settings.connection_name
            ):
                # Connection name on activity does not match that of setting.
                await context.send_activity(
                    self._get_token_exchange_invoke_response(
                        int(HTTPStatus.BAD_REQUEST),
                        "The bot received an InvokeActivity with a TokenExchangeInvokeRequest containing a"
                        " ConnectionName that does not match the ConnectionName expected by the bots active"
                        " OAuthPrompt. Ensure these names match when sending the InvokeActivity.",
                    )
                )
            else:
                # No errors. Proceed with token exchange.
                token_exchange_response = None
                try:
                    from microsoft_agents.hosting.dialogs._user_token_access import TokenExchangeRequest
                    token_exchange_response = await _UserTokenAccess.exchange_token(
                        context,
                        self._settings,
                        TokenExchangeRequest(token=token_value.token),
                    )
                except Exception:
                    # Ignore Exceptions
                    # If token exchange failed for any reason, tokenExchangeResponse above stays null
                    pass

                if not token_exchange_response or not token_exchange_response.token:
                    await context.send_activity(
                        self._get_token_exchange_invoke_response(
                            int(HTTPStatus.PRECONDITION_FAILED),
                            "The bot is unable to exchange token. Proceed with regular login.",
                        )
                    )
                else:
                    await context.send_activity(
                        self._get_token_exchange_invoke_response(
                            int(HTTPStatus.OK), None, token_value.id
                        )
                    )
                    token = TokenResponse(
                        channel_id=token_exchange_response.channel_id,
                        connection_name=token_exchange_response.connection_name,
                        token=token_exchange_response.token,
                        expiration=None,  # type: ignore[arg-type]
                    )
        elif context.activity.type == ActivityTypes.message and context.activity.text:
            match = re.match(r"(?<!\d)\d{6}(?!\d)", context.activity.text)
            if match:
                token = await _UserTokenAccess.get_user_token(
                    context, self._settings, match[0]
                )

        return (
            PromptRecognizerResult(True, token)
            if token is not None
            else PromptRecognizerResult()
        )

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
