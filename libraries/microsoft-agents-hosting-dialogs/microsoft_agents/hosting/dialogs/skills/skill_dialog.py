# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from copy import deepcopy
from typing import cast

from microsoft_agents.activity import (
    Activity,
    ActivityTypes,
    ExpectedReplies,
    DeliveryModes,
    OAuthCard,
    SignInConstants,
    TokenExchangeInvokeRequest,
)
from microsoft_agents.hosting.core import TurnContext, ChannelAdapter
from microsoft_agents.hosting.core.client import ConversationIdFactoryOptions
from microsoft_agents.hosting.core import CardFactory

from ..dialog import Dialog
from ..dialog_context import DialogContext
from ..models.dialog_events import DialogEvents
from ..models.dialog_reason import DialogReason
from ..models.dialog_instance import DialogInstance

from .begin_skill_dialog_options import BeginSkillDialogOptions
from .skill_dialog_options import SkillDialogOptions
from ..prompts.oauth_prompt_settings import OAuthPromptSettings
from .._user_token_access import _UserTokenAccess, TokenExchangeRequest

# Content type constant for OAuth cards
_OAUTH_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.oauth"


class SkillDialog(Dialog):
    SKILLCONVERSATIONIDSTATEKEY = (
        "Microsoft.Agents.Dialogs.SkillDialog.SkillConversationId"
    )

    def __init__(self, dialog_options: SkillDialogOptions, dialog_id: str):
        super().__init__(dialog_id)
        if not dialog_options:
            raise TypeError("SkillDialog.__init__(): dialog_options cannot be None.")

        self.dialog_options = dialog_options
        self._deliver_mode_state_key = "deliverymode"

    async def begin_dialog(self, dialog_context: DialogContext, options: object = None):
        """
        Method called when a new dialog has been pushed onto the stack and is being activated.
        """
        dialog_args = self._validate_begin_dialog_args(options)

        # Create deep clone of the original activity to avoid altering it before forwarding it.
        skill_activity: Activity = deepcopy(dialog_args.activity)

        # Apply conversation reference and common properties from incoming activity before sending.
        TurnContext.apply_conversation_reference(
            skill_activity,
            dialog_context.context.activity.get_conversation_reference(),
            is_incoming=True,
        )

        # Store delivery mode in dialog state for later use.
        assert dialog_context.active_dialog is not None
        dialog_context.active_dialog.state[self._deliver_mode_state_key] = (
            dialog_args.activity.delivery_mode
        )

        # Create the conversationId and store it in the dialog context state so we can use it later
        skill_conversation_id = await self._create_skill_conversation_id(
            dialog_context.context, dialog_context.context.activity
        )
        dialog_context.active_dialog.state[SkillDialog.SKILLCONVERSATIONIDSTATEKEY] = (
            skill_conversation_id
        )

        # Send the activity to the skill.
        eoc_activity = await self._send_to_skill(
            dialog_context.context, skill_activity, skill_conversation_id
        )
        if eoc_activity:
            return await dialog_context.end_dialog(eoc_activity.value)

        return self.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext):
        if not self._on_validate_activity(dialog_context.context.activity):
            return self.end_of_turn

        # Handle EndOfConversation from the skill
        if dialog_context.context.activity.type == ActivityTypes.end_of_conversation:
            return await dialog_context.end_dialog(
                dialog_context.context.activity.value
            )

        # Create deep clone of the original activity to avoid altering it before forwarding it.
        skill_activity = deepcopy(dialog_context.context.activity)

        assert dialog_context.active_dialog is not None
        skill_activity.delivery_mode = dialog_context.active_dialog.state[
            self._deliver_mode_state_key
        ]

        # Just forward to the remote skill
        skill_conversation_id = dialog_context.active_dialog.state[
            SkillDialog.SKILLCONVERSATIONIDSTATEKEY
        ]
        eoc_activity = await self._send_to_skill(
            dialog_context.context, skill_activity, skill_conversation_id
        )
        if eoc_activity:
            return await dialog_context.end_dialog(eoc_activity.value)

        return self.end_of_turn

    async def reprompt_dialog(  # pylint: disable=unused-argument
        self, context: TurnContext, instance: DialogInstance
    ):
        # Create and send an event to the skill so it can resume the dialog.
        reprompt_event = Activity(  # type: ignore[call-arg]
            type=ActivityTypes.event, name=DialogEvents.reprompt_dialog
        )

        # Apply conversation reference and common properties from incoming activity before sending.
        TurnContext.apply_conversation_reference(
            reprompt_event,
            context.activity.get_conversation_reference(),
            is_incoming=True,
        )

        skill_conversation_id = instance.state[SkillDialog.SKILLCONVERSATIONIDSTATEKEY]
        await self._send_to_skill(context, reprompt_event, skill_conversation_id)

    async def resume_dialog(  # pylint: disable=unused-argument
        self, dialog_context: "DialogContext", reason: DialogReason, result: object
    ):
        assert dialog_context.active_dialog is not None
        await self.reprompt_dialog(dialog_context.context, dialog_context.active_dialog)
        return self.end_of_turn

    async def end_dialog(
        self, context: TurnContext, instance: DialogInstance, reason: DialogReason
    ):
        # Send EndOfConversation to the skill if the dialog has been cancelled.
        if reason in (DialogReason.CancelCalled, DialogReason.ReplaceCalled):
            activity = Activity(type=ActivityTypes.end_of_conversation)  # type: ignore[call-arg]

            # Apply conversation reference and common properties from incoming activity before sending.
            TurnContext.apply_conversation_reference(
                activity,
                context.activity.get_conversation_reference(),
                is_incoming=True,
            )
            activity.channel_data = context.activity.channel_data

            skill_conversation_id = instance.state[
                SkillDialog.SKILLCONVERSATIONIDSTATEKEY
            ]
            await self._send_to_skill(context, activity, skill_conversation_id)

        await super().end_dialog(context, instance, reason)

    def _validate_begin_dialog_args(self, options: object) -> BeginSkillDialogOptions:
        if not options:
            raise TypeError("options cannot be None.")

        dialog_args = BeginSkillDialogOptions.from_object(options)

        if not dialog_args:
            raise TypeError(
                "SkillDialog: options object not valid as BeginSkillDialogOptions."
            )

        if not dialog_args.activity:
            raise TypeError(
                "SkillDialog: activity object in options as BeginSkillDialogOptions cannot be None."
            )

        return dialog_args

    def _on_validate_activity(
        self, activity: Activity  # pylint: disable=unused-argument
    ) -> bool:
        """
        Validates the activity sent during continue_dialog.
        Override this method to implement a custom validator for the activity being sent.
        """
        return True

    async def _send_to_skill(
        self, context: TurnContext, activity: Activity, skill_conversation_id: str
    ) -> Activity | None:
        if activity.type == ActivityTypes.invoke:
            # Force ExpectReplies for invoke activities so we can get the replies right away and send
            # them back to the channel if needed.
            activity.delivery_mode = DeliveryModes.expect_replies

        # Always save state before forwarding
        assert self.dialog_options.conversation_state is not None
        await self.dialog_options.conversation_state.save(context, True)

        assert self.dialog_options.skill is not None
        skill_info = self.dialog_options.skill
        response = await self.dialog_options.skill_client.post_activity(
            self.dialog_options.agent_id,
            skill_info.app_id,
            skill_info.endpoint,
            self.dialog_options.skill_host_endpoint,
            skill_conversation_id,
            activity,
        )

        # Inspect the skill response status
        if not 200 <= response.status <= 299:
            raise Exception(
                f'Error invoking the skill id: "{skill_info.id}" at'
                f' "{skill_info.endpoint}"'
                f" (status is {response.status}). \r\n {response.body}"
            )

        eoc_activity: Activity | None = None
        if activity.delivery_mode == DeliveryModes.expect_replies and response.body:
            # Process replies in the response.Body.
            raw_body = response.body
            expected_replies: ExpectedReplies | list[Activity] = (
                ExpectedReplies.model_validate(raw_body)
                if isinstance(raw_body, dict)
                else cast(list[Activity], raw_body)
            )
            activities: list[Activity] = (
                expected_replies.activities
                if isinstance(expected_replies, ExpectedReplies)
                else cast(list[Activity], expected_replies)
            )

            # Track sent invoke responses, so more than one is not sent.
            sent_invoke_response = False

            for from_skill_activity in activities:
                if from_skill_activity.type == ActivityTypes.end_of_conversation:
                    # Capture the EndOfConversation activity if it was sent from skill
                    eoc_activity = from_skill_activity

                    # The conversation has ended, so cleanup the conversation id
                    if self.dialog_options.conversation_id_factory is not None:
                        await self.dialog_options.conversation_id_factory.delete_conversation_reference(
                            skill_conversation_id
                        )
                elif not sent_invoke_response and await self._intercept_oauth_cards(
                    context, from_skill_activity, self.dialog_options.connection_name
                ):
                    # Token exchange succeeded, so no oauthcard needs to be shown to the user
                    sent_invoke_response = True
                else:
                    # If an invoke response has already been sent we should ignore future invoke responses
                    if from_skill_activity.type == ActivityTypes.invoke_response:
                        if sent_invoke_response:
                            continue
                        sent_invoke_response = True
                    # Send the response back to the channel.
                    await context.send_activity(from_skill_activity)

        return eoc_activity

    async def _create_skill_conversation_id(
        self, context: TurnContext, activity: Activity
    ) -> str:
        # Create a conversationId to interact with the skill
        assert self.dialog_options.skill is not None
        conversation_id_factory_options = ConversationIdFactoryOptions(
            from_oauth_scope=cast(
                str, context.turn_state.get(ChannelAdapter.OAUTH_SCOPE_KEY)
            )
            or "",
            from_agent_id=self.dialog_options.agent_id or "",
            activity=activity,
            agent=self.dialog_options.skill,
        )
        assert self.dialog_options.conversation_id_factory is not None
        skill_conversation_id = (
            await self.dialog_options.conversation_id_factory.create_conversation_id(
                conversation_id_factory_options
            )
        )
        return skill_conversation_id

    async def _intercept_oauth_cards(
        self, context: TurnContext, activity: Activity, connection_name: str | None
    ):
        """
        Tells if we should intercept the OAuthCard message.
        """
        if not connection_name or connection_name.isspace():
            return False

        if not activity.attachments:
            return False

        oauth_card_attachment = next(
            (
                attachment
                for attachment in activity.attachments
                if attachment.content_type == _OAUTH_CARD_CONTENT_TYPE
            ),
            None,
        )
        if oauth_card_attachment is None:
            return False

        oauth_card = cast(OAuthCard, oauth_card_attachment.content)
        if (
            not oauth_card
            or not oauth_card.token_exchange_resource
            or not oauth_card.token_exchange_resource.uri
        ):
            return False

        try:
            settings = OAuthPromptSettings(
                connection_name=connection_name, title="Sign In"
            )
            result = await _UserTokenAccess.exchange_token(
                context,
                settings,
                TokenExchangeRequest(uri=oauth_card.token_exchange_resource.uri),
            )

            if not result or not result.token:
                return False

            # If not, send an invoke to the skill with the token.
            return await self._send_token_exchange_invoke_to_skill(
                activity,
                oauth_card.token_exchange_resource.id,
                oauth_card.connection_name,
                result.token,
            )
        except Exception:
            # Failures in token exchange are not fatal.
            return False

    async def _send_token_exchange_invoke_to_skill(
        self,
        incoming_activity: Activity,
        request_id: str,
        connection_name: str,
        token: str,
    ):
        activity = cast(Activity, incoming_activity.create_reply())
        activity.type = ActivityTypes.invoke
        activity.name = SignInConstants.token_exchange_operation_name
        activity.value = TokenExchangeInvokeRequest(
            id=request_id,
            token=token,
            connection_name=connection_name,
        )

        # route the activity to the skill
        assert self.dialog_options.skill is not None
        skill_info = self.dialog_options.skill
        response = await self.dialog_options.skill_client.post_activity(
            self.dialog_options.agent_id,
            skill_info.app_id,
            skill_info.endpoint,
            self.dialog_options.skill_host_endpoint,
            incoming_activity.conversation.id,
            activity,
        )

        return 200 <= response.status <= 299
