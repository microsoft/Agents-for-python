import logging
from asyncio import Awaitable
from microsoft.agents.hosting.core import (
    ActivityHandler,
    AgentState,
    TurnContext,
)
from microsoft.agents.hosting.dialogs import Dialog

logger = logging.getLogger(__name__)

class DialogAgent(ActivityHandler):

    def __init__(self, conversation_state: AgentState, user_state: AgentState, dialog: Dialog):
        super().__init__()
        if not conversation_state: raise ValueError("DialogBot: Missing parameter. conversation_state is required")
        if not user_state: raise ValueError("DialogBot: Missing parameter. user_state is required")
        if not dialog: raise ValueError("DialogBot: Missing parameter. dialog is required")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_state = self.conversation_state.create_property("DialogState")

    async def on_message(self, context: TurnContext, next: Awaitable):
        logger.debug("Running dialog with Message Activity.")
        await self.dialog.run(context, self.dialog_state)
        await next()

    async def on_dialog(self, context: TurnContext, next: Awaitable):
        await self.conversation_state.save_changes(context, False)
        await self.user_state.save_changes(context, False)
        await next()