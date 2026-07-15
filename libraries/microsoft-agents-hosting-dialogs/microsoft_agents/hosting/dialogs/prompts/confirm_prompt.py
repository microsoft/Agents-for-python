# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Callable

from recognizers_choice import recognize_boolean

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes, Activity

from ..choices import (
    Choice,
    ChoiceFactoryOptions,
    ChoiceRecognizers,
    ListStyle,
)

from .prompt import Prompt
from .prompt_culture_models import PromptCultureModels
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult
from .prompt_validator_context import PromptValidatorContext


class ConfirmPrompt(Prompt):
    """Prompts a user to confirm something with a yes/no response.

    The prompt first attempts to recognise a boolean value using the
    ``recognizers_choice`` package (e.g. "yes", "no", "true", "false", locale
    equivalents).  If that fails and the prompt was configured to include
    numbered choices (the default), it falls back to matching choice indices
    ("1" → yes, "2" → no).

    Returns ``True`` for confirmation, ``False`` for denial.

    Culture/locale detection uses :class:`microsoft_agents.hosting.dialogs.PromptCultureModels`.  Override
    ``default_locale`` or ``choice_defaults`` at construction time to customise
    the displayed choices and the locale used for recognition.
    """

    _default_choice_options: dict[str, tuple[Choice, Choice, ChoiceFactoryOptions]] = {
        c.locale: (
            Choice(c.yes_in_language),
            Choice(c.no_in_language),
            ChoiceFactoryOptions(c.separator, c.inline_or, c.inline_or_more, True),
        )
        for c in PromptCultureModels.get_supported_cultures()
    }

    def __init__(
        self,
        dialog_id: str,
        validator: Callable[[PromptValidatorContext], Any] | None = None,
        default_locale: str | None = None,
        choice_defaults: (
            dict[str, tuple[Choice, Choice, ChoiceFactoryOptions]] | None
        ) = None,
    ):
        super().__init__(dialog_id, validator)
        if dialog_id is None:
            raise TypeError("ConfirmPrompt(): dialog_id cannot be None.")
        self.style = ListStyle.auto
        self.default_locale = default_locale
        self.choice_options = None
        self.confirm_choices = None

        if choice_defaults is not None:
            self._default_choice_options = choice_defaults

    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        if not turn_context:
            raise TypeError("ConfirmPrompt.on_prompt(): turn_context cannot be None.")
        if not options:
            raise TypeError("ConfirmPrompt.on_prompt(): options cannot be None.")

        # Format prompt to send
        channel_id = turn_context.activity.channel_id or ""
        culture = self._determine_culture(turn_context.activity)
        defaults = self._default_choice_options[culture]
        choice_opts = (
            self.choice_options if self.choice_options is not None else defaults[2]
        )
        confirms = (
            self.confirm_choices
            if self.confirm_choices is not None
            else (defaults[0], defaults[1])
        )
        choices = [confirms[0], confirms[1]]
        if is_retry and options.retry_prompt is not None:
            prompt = self.append_choices(
                options.retry_prompt, channel_id, choices, self.style, choice_opts
            )
        else:
            prompt = self.append_choices(
                options.prompt, channel_id, choices, self.style, choice_opts
            )
        await turn_context.send_activity(prompt)

    async def on_recognize(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
    ) -> PromptRecognizerResult:
        if not turn_context:
            raise TypeError("ConfirmPrompt.on_prompt(): turn_context cannot be None.")

        result = PromptRecognizerResult()
        if turn_context.activity.type == ActivityTypes.message:
            # Recognize utterance
            utterance = turn_context.activity.text
            if not utterance:
                return result
            culture = self._determine_culture(turn_context.activity)
            results = recognize_boolean(utterance, culture)
            if results:
                first = results[0]
                if "value" in first.resolution:
                    result.succeeded = True
                    result.value = first.resolution["value"]
            else:
                # First check whether the prompt was sent to the user with numbers
                defaults = self._default_choice_options[culture]
                opts = (
                    self.choice_options
                    if self.choice_options is not None
                    else defaults[2]
                )

                if opts.include_numbers is None or opts.include_numbers:
                    confirm_choices = (
                        self.confirm_choices
                        if self.confirm_choices is not None
                        else (defaults[0], defaults[1])
                    )
                    choices = [confirm_choices[0], confirm_choices[1]]
                    second_attempt_results = ChoiceRecognizers.recognize_choices(
                        utterance, choices
                    )
                    if second_attempt_results:
                        result.succeeded = True
                        result.value = second_attempt_results[0].resolution.index == 0

        return result

    def _determine_culture(self, activity: Activity) -> str:
        culture = (
            PromptCultureModels.map_to_nearest_language(activity.locale)
            or self.default_locale
            or PromptCultureModels.English.locale
        )
        if not culture or not self._default_choice_options.get(culture):
            culture = PromptCultureModels.English.locale

        return culture
