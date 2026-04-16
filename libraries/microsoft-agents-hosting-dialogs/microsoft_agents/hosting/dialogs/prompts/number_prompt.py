# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, cast

from recognizers_number import recognize_number
from recognizers_text import Culture, ModelResult
from babel.numbers import parse_decimal

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes

from .prompt import Prompt, PromptValidatorContext
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult


class NumberPrompt(Prompt):
    def __init__(
        self,
        dialog_id: str,
        validator: Callable[[PromptValidatorContext], bool] | None = None,
        default_locale: str | None = None,
    ):
        super(NumberPrompt, self).__init__(dialog_id, validator)
        self.default_locale = default_locale

    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        if not turn_context:
            raise TypeError("NumberPrompt.on_prompt(): turn_context cannot be None.")
        if not options:
            raise TypeError("NumberPrompt.on_prompt(): options cannot be None.")

        if is_retry and options.retry_prompt is not None:
            await turn_context.send_activity(options.retry_prompt)
        elif options.prompt is not None:
            await turn_context.send_activity(options.prompt)

    async def on_recognize(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
    ) -> PromptRecognizerResult:
        if not turn_context:
            raise TypeError("NumberPrompt.on_recognize(): turn_context cannot be None.")

        result = PromptRecognizerResult()
        if turn_context.activity.type == ActivityTypes.message:
            utterance = turn_context.activity.text
            if not utterance:
                return result
            culture = self._get_culture(turn_context)
            results: list[ModelResult] = recognize_number(utterance, culture)

            if results:
                result.succeeded = True
                result.value = parse_decimal(
                    cast(str, results[0].resolution["value"]), locale=culture.replace("-", "_")
                )

        return result

    def _get_culture(self, turn_context: TurnContext):
        culture = (
            turn_context.activity.locale
            if turn_context.activity.locale
            else self.default_locale
        )

        if not culture:
            culture = Culture.English

        return culture
