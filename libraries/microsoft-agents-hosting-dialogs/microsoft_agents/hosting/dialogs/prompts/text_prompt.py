# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes

from .prompt import Prompt
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult


class TextPrompt(Prompt):
    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        if not turn_context:
            raise TypeError("TextPrompt.on_prompt(): turn_context cannot be None.")
        if not options:
            raise TypeError("TextPrompt.on_prompt(): options cannot be None.")

        if is_retry and options.retry_prompt is not None:
            await turn_context.send_activity(options.retry_prompt)
        else:
            if options.prompt is not None:
                await turn_context.send_activity(options.prompt)

    async def on_recognize(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
    ) -> PromptRecognizerResult:
        if not turn_context:
            raise TypeError(
                "TextPrompt.on_recognize(): turn_context cannot be None."
            )

        result = PromptRecognizerResult()
        if turn_context.activity.type == ActivityTypes.message:
            message = turn_context.activity
            if message.text is not None:
                result.succeeded = True
                result.value = message.text
        return result
