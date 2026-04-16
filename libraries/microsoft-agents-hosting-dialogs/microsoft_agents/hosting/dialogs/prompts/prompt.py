# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import abstractmethod
import copy
from typing import Any, Callable, Awaitable, cast

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import InputHints, ActivityTypes, Activity

from ..choices import (
    Choice,
    ChoiceFactory,
    ChoiceFactoryOptions,
    ListStyle,
)
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult
from .prompt_validator_context import PromptValidatorContext
from ..models.dialog_reason import DialogReason
from ..dialog import Dialog
from ..models.dialog_instance import DialogInstance
from ..models.dialog_turn_result import DialogTurnResult
from ..dialog_context import DialogContext


class Prompt(Dialog):
    """
    Defines the core behavior of prompt dialogs. Extends the Dialog base class.
    """

    ATTEMPT_COUNT_KEY = "AttemptCount"
    persisted_options = "options"
    persisted_state = "state"

    def __init__(self, dialog_id: str, validator: Callable[[PromptValidatorContext], Any] | None = None):
        """
        Creates a new Prompt instance.
        """
        super(Prompt, self).__init__(dialog_id)
        self._validator = validator

    async def begin_dialog(
        self, dialog_context: DialogContext, options: object = None
    ) -> DialogTurnResult:
        if not dialog_context:
            raise TypeError("Prompt(): dc cannot be None.")
        if not isinstance(options, PromptOptions):
            raise TypeError("Prompt(): Prompt options are required for Prompt dialogs.")

        # Ensure prompts have input hint set
        if options.prompt is not None and not options.prompt.input_hint:
            options.prompt.input_hint = InputHints.expecting_input

        if options.retry_prompt is not None and not options.retry_prompt.input_hint:
            options.retry_prompt.input_hint = InputHints.expecting_input

        # Initialize prompt state
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state
        state[self.persisted_options] = options
        state[self.persisted_state] = {}

        # Send initial prompt
        await self.on_prompt(
            dialog_context.context,
            state[self.persisted_state],
            state[self.persisted_options],
            False,
        )

        return Dialog.end_of_turn

    async def continue_dialog(self, dialog_context: DialogContext):
        if not dialog_context:
            raise TypeError("Prompt(): dc cannot be None.")

        # Don't do anything for non-message activities
        if dialog_context.context.activity.type != ActivityTypes.message:
            return Dialog.end_of_turn

        # Perform base recognition
        instance = dialog_context.active_dialog
        assert instance is not None
        state = cast(dict[str, object], instance.state[self.persisted_state])
        options = cast(PromptOptions, instance.state[self.persisted_options])
        recognized = await self.on_recognize(dialog_context.context, state, options)

        # Validate the return value
        is_valid = False
        if self._validator is not None:
            prompt_context = PromptValidatorContext(
                dialog_context.context, recognized, state, options
            )
            is_valid = await self._validator(prompt_context)
            if options is None:
                options = PromptOptions()
            options.number_of_attempts += 1
        else:
            if recognized.succeeded:
                is_valid = True

        # Return recognized value or re-prompt
        if is_valid:
            return await dialog_context.end_dialog(recognized.value)

        if not dialog_context.context.responded:
            await self.on_prompt(dialog_context.context, state, options, True)
        return Dialog.end_of_turn

    async def resume_dialog(
        self, dialog_context: DialogContext, reason: DialogReason, result: object
    ) -> DialogTurnResult:
        assert dialog_context.active_dialog is not None
        await self.reprompt_dialog(dialog_context.context, dialog_context.active_dialog)
        return Dialog.end_of_turn

    async def reprompt_dialog(self, context: TurnContext, instance: DialogInstance):
        state = instance.state[self.persisted_state]
        options = instance.state[self.persisted_options]
        await self.on_prompt(context, state, options, False)

    @abstractmethod
    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        pass

    @abstractmethod
    async def on_recognize(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
    ) -> PromptRecognizerResult:
        pass

    def append_choices(
        self,
        prompt: Activity | None,
        channel_id: str,
        choices: list[Choice],
        style: ListStyle | int,
        options: ChoiceFactoryOptions | None = None,
    ) -> Activity:
        """
        Composes an output activity containing a set of choices.
        """
        # Get base prompt text (if any)
        text = prompt.text if prompt is not None and prompt.text else ""

        # Create temporary msg
        def inline() -> Activity:
            return ChoiceFactory.inline(choices, text, None, options)

        def list_style() -> Activity:
            return ChoiceFactory.list_style(choices, text, None, options)

        def suggested_action() -> Activity:
            return ChoiceFactory.suggested_action(choices, text)

        def hero_card() -> Activity:
            return ChoiceFactory.hero_card(choices, text)

        def list_style_none() -> Activity:
            from microsoft_agents.activity import Activity as _Activity, ActivityTypes as _AT
            activity = _Activity(type=_AT.message)  # type: ignore[call-arg]
            activity.text = text
            return activity

        def default() -> Activity:
            return ChoiceFactory.for_channel(channel_id, choices, text, None, options)

        # Maps to values in ListStyle Enum
        switcher = {
            0: list_style_none,
            1: default,
            2: inline,
            3: list_style,
            4: suggested_action,
            5: hero_card,
        }

        msg = switcher.get(int(style), default)()

        # Update prompt with text, actions and attachments
        if prompt:
            # clone the prompt set in the options
            prompt = copy.copy(prompt)

            prompt.text = msg.text

            if (
                msg.suggested_actions is not None
                and msg.suggested_actions.actions is not None
                and msg.suggested_actions.actions
            ):
                prompt.suggested_actions = msg.suggested_actions

            if msg.attachments:
                if prompt.attachments:
                    prompt.attachments.extend(msg.attachments)
                else:
                    prompt.attachments = msg.attachments

            return prompt

        msg.input_hint = None  # type: ignore[assignment]
        return msg
