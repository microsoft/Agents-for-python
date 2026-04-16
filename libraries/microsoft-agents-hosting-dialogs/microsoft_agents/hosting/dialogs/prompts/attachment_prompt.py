# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes

from .prompt import Prompt, PromptValidatorContext
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult


class AttachmentPrompt(Prompt):
    """
    Prompts a user to upload attachments like images.

    By default the prompt will return to the calling dialog an `[Attachment]`
    """

    def __init__(
        self,
        dialog_id: str,
        validator: Callable[[PromptValidatorContext], bool] | None = None,
    ):
        super().__init__(dialog_id, validator)

    async def on_prompt(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
        is_retry: bool,
    ):
        """Sends the initial or retry prompt activity to the user.

        :param turn_context: The context for the current turn.
        :param state: Persisted prompt state (unused by AttachmentPrompt).
        :param options: Prompt options containing the prompt and optional retry prompt.
        :param is_retry: ``True`` when re-prompting after failed validation.
        """
        if not turn_context:
            raise TypeError("AttachmentPrompt.on_prompt(): TurnContext cannot be None.")

        if not isinstance(options, PromptOptions):
            raise TypeError(
                "AttachmentPrompt.on_prompt(): PromptOptions are required for Attachment Prompt dialogs."
            )

        if is_retry and options.retry_prompt:
            await turn_context.send_activity(options.retry_prompt)
        elif options.prompt:
            await turn_context.send_activity(options.prompt)

    async def on_recognize(
        self,
        turn_context: TurnContext,
        state: dict[str, object],
        options: PromptOptions,
    ) -> PromptRecognizerResult:
        """Attempts to recognise attachments from the incoming activity.

        Succeeds only when the activity is a message **and** ``activity.attachments``
        is a non-empty list.  The full attachment list is returned as the result.

        .. note::
            A message activity with no attachments (e.g. plain text) will fail
            recognition and trigger the retry prompt.

        :param turn_context: The context for the current turn.
        :param state: Persisted prompt state (unused by AttachmentPrompt).
        :param options: Prompt options (unused by AttachmentPrompt).
        :return: Recognition result with ``succeeded=True`` and the list of
            :class:`Attachment` objects, or ``succeeded=False`` if none were found.
        """
        if not turn_context:
            raise TypeError("AttachmentPrompt.on_recognize(): context cannot be None.")

        result = PromptRecognizerResult()

        if turn_context.activity.type == ActivityTypes.message:
            message = turn_context.activity
            if isinstance(message.attachments, list) and message.attachments:
                result.succeeded = True
                result.value = message.attachments

        return result
