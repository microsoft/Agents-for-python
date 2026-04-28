# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
)
from microsoft_agents.hosting.dialogs import Dialog
from .dialog_helper import DialogHelper


class DialogAgent(ActivityHandler):
    """
    This Agent implementation can run any type of Dialog. The use of type parameterization is to allows multiple
    different agents to be run at different endpoints within the same project. This can be achieved by defining distinct
    Controller types each with dependency on distinct Agent types. The ConversationState is used by the Dialog system. The
    UserState isn't, however, it might have been used in a Dialog implementation, and the requirement is that all
    AgentState objects are saved at the end of a turn.
    """

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ):
        if conversation_state is None:
            raise TypeError(
                "[DialogAgent]: Missing parameter. conversation_state is required but None was given"
            )
        if user_state is None:
            raise TypeError(
                "[DialogAgent]: Missing parameter. user_state is required but None was given"
            )
        if dialog is None:
            raise Exception("[DialogAgent]: Missing parameter. dialog is required")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        # Save any state changes that might have ocurred during the turn.
        await self.conversation_state.save(turn_context)
        await self.user_state.save(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("DialogState"),
        )

    async def on_invoke_activity(self, turn_context: TurnContext):
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("DialogState"),
        )