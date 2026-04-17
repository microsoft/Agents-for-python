# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import MessageFactory
from microsoft_agents.hosting.dialogs import PromptOptions


class SlotDetails:
    def __init__(
        self,
        name: str,
        dialog_id: str,
        options: PromptOptions | None = None,
        prompt: str = "",
        retry_prompt: str | None = None,
    ):
        self.name = name
        self.dialog_id = dialog_id
        self.options = (
            options
            if options
            else PromptOptions(
                prompt=MessageFactory.text(prompt),
                retry_prompt=None
                if retry_prompt is None
                else MessageFactory.text(retry_prompt),
            )
        )