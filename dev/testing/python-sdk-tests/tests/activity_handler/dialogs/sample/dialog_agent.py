# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""DialogAgent — generic ActivityHandler that drives a single root Dialog."""

from microsoft_agents.hosting.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
)
from microsoft_agents.hosting.dialogs import Dialog, DialogSet, DialogTurnStatus


class DialogAgent(ActivityHandler):
    """ActivityHandler that routes every message turn through a dialog."""

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ) -> None:
        super().__init__()
        if conversation_state is None:
            raise TypeError("conversation_state is required")
        if user_state is None:
            raise TypeError("user_state is required")
        if dialog is None:
            raise TypeError("dialog is required")

        self._conversation_state = conversation_state
        self._user_state = user_state
        self._dialog = dialog
        self._dialog_state = conversation_state.create_property("DialogState")

    async def on_turn(self, turn_context: TurnContext) -> None:
        await super().on_turn(turn_context)
        await self._conversation_state.save(turn_context)
        await self._user_state.save(turn_context)

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        dialog_set = DialogSet(self._dialog_state)
        dialog_set.add(self._dialog)

        dc = await dialog_set.create_context(turn_context)
        results = await dc.continue_dialog()
        if results.status == DialogTurnStatus.Empty:
            await dc.begin_dialog(self._dialog.id)
