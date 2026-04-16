# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from typing import Dict, cast
from microsoft_agents.hosting.core import TurnContext
from .prompt_options import PromptOptions
from .prompt_recognizer_result import PromptRecognizerResult


class PromptValidatorContext:
    def __init__(
        self,
        turn_context: TurnContext,
        recognized: PromptRecognizerResult,
        state: Dict[str, object],
        options: PromptOptions,
    ):
        """Creates contextual information passed to a custom `PromptValidator`.
        Parameters
        ----------
        turn_context
            The context for the current turn of conversation with the user.
        recognized
            Result returned from the prompts recognizer function.
        state
            A dictionary of values persisted for each conversational turn while the prompt is active.
        options
            Original set of options passed to the prompt by the calling dialog.
        """
        self.context = turn_context
        self.recognized = recognized
        self.state = state
        self.options = options

    @property
    def attempt_count(self) -> int:
        """Gets the number of times ``continue_dialog`` has been called on this prompt.

        .. warning:: **Behaviour differs between prompt types:**

            * :class:`ActivityPrompt` increments the counter in persisted state
              *before* calling the validator, so ``attempt_count`` is at least 1
              on the first validation call.
            * The base :class:`Prompt` class (and all its subclasses —
              :class:`TextPrompt`, :class:`NumberPrompt`, :class:`ChoicePrompt`,
              etc.) does **not** store this key in state, so ``attempt_count``
              is always **0** regardless of how many times the user has been
              prompted.  Use :attr:`PromptOptions.number_of_attempts` for
              reliable attempt tracking in those prompts.
        """
        # pylint: disable=import-outside-toplevel
        from microsoft_agents.hosting.dialogs.prompts.prompt import Prompt

        return int(cast(int, self.state.get(Prompt.ATTEMPT_COUNT_KEY, 0)))
