# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes

from .prompt import Prompt
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult


class TextPrompt(Prompt):
    """Prompts a user to enter any text.

    Succeeds whenever the user sends a message activity whose ``text`` field is
    not ``None``.  Empty strings are accepted as valid because some channels
    send an empty ``text`` alongside attachments.  There is no built-in
    recognizer: the raw ``activity.text`` string is returned as the result.

    Pass an optional ``validator`` at construction time to apply additional
    constraints (e.g. minimum length, allow-list, non-empty enforcement).

    .. note::
        Non-message activities and messages where ``activity.text`` is ``None``
        cause recognition to fail and will trigger the retry prompt if one was
        provided.
    """

    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        """Sends the initial or retry prompt activity to the user.

        :param turn_context: The context for the current turn.
        :param state: Persisted prompt state (unused by TextPrompt).
        :param options: Prompt options containing the prompt and optional retry prompt.
        :param is_retry: ``True`` when re-prompting after a failed validation.
        """
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
        """Attempts to recognise text from the incoming activity.

        Succeeds only when the activity is a message **and** ``activity.text``
        is not ``None``.  Empty strings are considered valid (``succeeded=True``
        with an empty string value), since some channels send empty text with
        attachments.

        :param turn_context: The context for the current turn.
        :param state: Persisted prompt state (unused by TextPrompt).
        :param options: Prompt options (unused by TextPrompt).
        :return: Recognition result with ``succeeded=True`` and the raw text when
            a message with text is received; ``succeeded=False`` otherwise.
        """
        if not turn_context:
            raise TypeError("TextPrompt.on_recognize(): turn_context cannot be None.")

        result = PromptRecognizerResult()
        if turn_context.activity.type == ActivityTypes.message:
            message = turn_context.activity
            if message.text is not None:
                result.succeeded = True
                result.value = message.text
        return result
