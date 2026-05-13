# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.dialogs.choices import Choice, ListStyle


class PromptOptions:
    """
    Contains settings to pass to a :class:`microsoft_agents.hosting.dialogs.Prompt` object when the prompt is started.
    """

    def __init__(
        self,
        prompt: Activity | None = None,
        retry_prompt: Activity | None = None,
        choices: list[Choice] | None = None,
        style: ListStyle | None = None,
        validations: object = None,
        number_of_attempts: int = 0,
    ):
        """
        Contains settings to pass to a :class:`microsoft_agents.hosting.dialogs.Prompt` when the prompt is started.

        :param prompt: The initial prompt activity to send to the user.
        :type prompt: :class:`microsoft_agents.activity.Activity`
        :param retry_prompt: The activity to send when the user's input fails validation.
        :type retry_prompt: :class:`microsoft_agents.activity.Activity`
        :param choices: The list of choices presented to the user (used by :class:`microsoft_agents.hosting.dialogs.ChoicePrompt`).
        :type choices: list[:class:`microsoft_agents.hosting.dialogs.choices.Choice`]
        :param style: Controls how the choice list is rendered.
        :type style: :class:`microsoft_agents.hosting.dialogs.choices.ListStyle`
        :param validations: Additional validation data passed through to a custom validator.
        :param number_of_attempts: Running count of how many times the prompt has been retried.
        :type number_of_attempts: int
        """
        self.prompt = prompt
        self.retry_prompt = retry_prompt
        self.choices = choices
        self.style = style
        self.validations = validations
        self.number_of_attempts = number_of_attempts
