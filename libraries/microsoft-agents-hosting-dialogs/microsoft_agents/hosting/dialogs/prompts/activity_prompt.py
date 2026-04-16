# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Callable, cast

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes, InputHints

from ..dialog import Dialog
from ..dialog_context import DialogContext
from ..models.dialog_instance import DialogInstance
from ..models.dialog_reason import DialogReason
from ..models.dialog_turn_result import DialogTurnResult
from .prompt import Prompt
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult
from .prompt_validator_context import PromptValidatorContext


class ActivityPrompt(Dialog):
    """
    Waits for an activity to be received.

    This prompt requires a validator be passed in and is useful when waiting for non-message
    activities like an event to be received. The validator can ignore received events until the
    expected activity is received.
    """

    persisted_options = "options"
    persisted_state = "state"

    def __init__(
        self, dialog_id: str, validator: Callable[[PromptValidatorContext], Any]
    ):
        Dialog.__init__(self, dialog_id)

        if validator is None:
            raise TypeError("validator was expected but received None")
        self._validator = validator

    async def begin_dialog(
        self, dialog_context: DialogContext, options: object = None
    ) -> DialogTurnResult:
        if not dialog_context:
            raise TypeError("ActivityPrompt.begin_dialog(): dc cannot be None.")
        if not isinstance(options, PromptOptions):
            raise TypeError(
                "ActivityPrompt.begin_dialog(): Prompt options are required for ActivityPrompts."
            )

        # Ensure prompts have input hint set
        if options.prompt is not None and not options.prompt.input_hint:
            options.prompt.input_hint = InputHints.expecting_input

        if options.retry_prompt is not None and not options.retry_prompt.input_hint:
            options.retry_prompt.input_hint = InputHints.expecting_input

        # Initialize prompt state
        assert dialog_context.active_dialog is not None
        state: dict[str, object] = dialog_context.active_dialog.state
        state[self.persisted_options] = options
        state[self.persisted_state] = {Prompt.ATTEMPT_COUNT_KEY: 0}

        # Send initial prompt
        await self.on_prompt(
            dialog_context.context,
            cast(dict[str, object], state[self.persisted_state]),
            cast(PromptOptions, state[self.persisted_options]),
            False,
        )

        return Dialog.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext) -> DialogTurnResult:
        if not dialog_context:
            raise TypeError(
                "ActivityPrompt.continue_dialog(): DialogContext cannot be None."
            )

        # Perform base recognition
        instance = dialog_context.active_dialog
        assert instance is not None
        state: dict[str, object] = cast(
            dict[str, object], instance.state[self.persisted_state]
        )
        prompt_options: PromptOptions = cast(
            PromptOptions, instance.state[self.persisted_options]
        )
        recognized: PromptRecognizerResult = await self.on_recognize(
            dialog_context.context, state, prompt_options
        )

        # Increment attempt count
        state[Prompt.ATTEMPT_COUNT_KEY] = (
            int(cast(int, state.get(Prompt.ATTEMPT_COUNT_KEY, 0))) + 1
        )

        # Validate the return value
        is_valid = False
        if self._validator is not None:
            prompt_context = PromptValidatorContext(
                dialog_context.context, recognized, state, prompt_options
            )
            is_valid = await self._validator(prompt_context)

            prompt_options.number_of_attempts += 1
        elif recognized.succeeded:
            is_valid = True

        # Return recognized value or re-prompt
        if is_valid:
            return await dialog_context.end_dialog(recognized.value)

        if (
            dialog_context.context.activity.type == ActivityTypes.message
            and not dialog_context.context.responded
        ):
            await self.on_prompt(dialog_context.context, state, prompt_options, True)

        return Dialog.end_of_turn

    async def resume_dialog(  # pylint: disable=unused-argument
        self, dialog_context: DialogContext, reason: DialogReason, result: object = None
    ):
        assert dialog_context.active_dialog is not None
        await self.reprompt_dialog(dialog_context.context, dialog_context.active_dialog)

        return Dialog.end_of_turn

    async def reprompt_dialog(self, context: TurnContext, instance: DialogInstance):
        state: dict[str, object] = instance.state[self.persisted_state]
        options: PromptOptions = instance.state[self.persisted_options]
        await self.on_prompt(context, state, options, False)

    async def on_prompt(
        self,
        context: TurnContext,
        state: dict[str, object],  # pylint: disable=unused-argument
        options: PromptOptions,
        is_retry: bool = False,
    ):
        if is_retry and options.retry_prompt:
            options.retry_prompt.input_hint = InputHints.expecting_input
            await context.send_activity(options.retry_prompt)
        elif options.prompt:
            options.prompt.input_hint = InputHints.expecting_input
            await context.send_activity(options.prompt)

    async def on_recognize(  # pylint: disable=unused-argument
        self, context: TurnContext, state: dict[str, object], options: PromptOptions
    ) -> PromptRecognizerResult:
        result = PromptRecognizerResult()
        result.succeeded = True
        result.value = context.activity

        return result
