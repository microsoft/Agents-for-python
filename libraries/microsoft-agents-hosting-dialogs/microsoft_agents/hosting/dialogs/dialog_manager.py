# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from datetime import datetime, timedelta
from threading import Lock

from microsoft_agents.hosting.core import (
    ChannelAdapter,
    ConversationState,
    UserState,
    TurnContext,
)

from .dialog import Dialog
from .dialog_context import DialogContext
from .dialog_events import DialogEvents
from .dialog_extensions import DialogExtensions
from .dialog_set import DialogSet
from .dialog_state import DialogState
from .dialog_manager_result import DialogManagerResult
from .dialog_turn_status import DialogTurnStatus
from .dialog_turn_result import DialogTurnResult


class DialogManager:
    """
    Class which runs the dialog system.
    """

    def __init__(self, root_dialog: Dialog = None, dialog_state_property: str = None):
        """
        Initializes an instance of the DialogManager class.
        :param root_dialog: Root dialog to use.
        :param dialog_state_property: Alternate name for the dialog_state property. (Default is "DialogState").
        """
        self.last_access = "_lastAccess"
        self._root_dialog_id = ""
        self._dialog_state_property = dialog_state_property or "DialogState"
        self._lock = Lock()

        # Gets or sets root dialog to use to start conversation.
        self.root_dialog = root_dialog

        # Gets or sets the ConversationState.
        self.conversation_state: ConversationState = None

        # Gets or sets the UserState.
        self.user_state: UserState = None

        # Gets InitialTurnState collection to copy into the TurnState on every turn.
        self.initial_turn_state = {}

        # Gets or sets global dialogs that you want to have be callable.
        self.dialogs = DialogSet()

        # Gets or sets (optional) number of milliseconds to expire the bot's state after.
        self.expire_after: int = None

    async def on_turn(self, context: TurnContext) -> DialogManagerResult:
        """
        Runs dialog system in the context of a TurnContext.
        :param context: turn context.
        :return:
        """
        # Lazy initialize RootDialog so it can refer to assets like LG function templates
        if not self._root_dialog_id:
            with self._lock:
                if not self._root_dialog_id:
                    self._root_dialog_id = self.root_dialog.id
                    self.dialogs.add(self.root_dialog)

        # Preload TurnState with DM TurnState.
        for key, val in self.initial_turn_state.items():
            context.turn_state[key] = val

        # Register DialogManager with TurnState.
        context.turn_state[DialogManager.__name__] = self

        # Resolve ConversationState
        conversation_state_name = ConversationState.__name__
        if self.conversation_state is None:
            if conversation_state_name not in context.turn_state:
                raise Exception(
                    f"Unable to get an instance of {conversation_state_name} from turn_context. "
                    f"Please ensure ConversationState is available in turn_state."
                )
            self.conversation_state = context.turn_state[conversation_state_name]
        else:
            context.turn_state[conversation_state_name] = self.conversation_state

        # Resolve UserState (optional)
        user_state_name = UserState.__name__
        if self.user_state is None:
            self.user_state = context.turn_state.get(user_state_name, None)
        else:
            context.turn_state[user_state_name] = self.user_state

        # Create property accessors
        last_access_property = self.conversation_state.create_property(self.last_access)
        last_access: datetime = await last_access_property.get(context, datetime.now)

        # Check for expired conversation
        if self.expire_after is not None and (
            datetime.now() - last_access
        ) >= timedelta(milliseconds=float(self.expire_after)):
            # Clear conversation state
            self.conversation_state.clear(context)

        last_access = datetime.now()
        await last_access_property.set(context, last_access)

        # Get dialog stack
        dialogs_property = self.conversation_state.create_property(
            self._dialog_state_property
        )
        dialog_state: DialogState = await dialogs_property.get(context, DialogState)

        # Create DialogContext
        dialog_context = DialogContext(self.dialogs, context, dialog_state)

        # Call the common dialog "continue/begin" execution pattern shared with the classic RunAsync extension method
        turn_result = await DialogExtensions._internal_run(  # pylint: disable=protected-access
            context, self._root_dialog_id, dialog_context
        )

        # Save ConversationState changes
        await self.conversation_state.save(context, False)

        # Save UserState changes if present
        if self.user_state is not None:
            await self.user_state.save(context, False)

        return DialogManagerResult(turn_result=turn_result)

    @staticmethod
    def is_from_parent_to_skill(turn_context: TurnContext) -> bool:
        """
        Determines if this turn is a request from a parent bot to this skill.
        """
        from microsoft_agents.hosting.core import ClaimsIdentity

        claims_identity = turn_context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY, None
        )
        return isinstance(
            claims_identity, ClaimsIdentity
        ) and claims_identity.is_agent_claim()

    @staticmethod
    def should_send_end_of_conversation_to_parent(
        context: TurnContext, turn_result: DialogTurnResult
    ) -> bool:
        """
        Helper to determine if we should send an EndOfConversation to the parent or not.
        """
        if not (
            turn_result.status == DialogTurnStatus.Complete
            or turn_result.status == DialogTurnStatus.Cancelled
        ):
            # The dialog is still going, don't return EoC.
            return False

        return DialogManager.is_from_parent_to_skill(context)

    @staticmethod
    def get_active_dialog_context(dialog_context: DialogContext) -> DialogContext:
        """
        Recursively walk up the DC stack to find the active DC.
        """
        return DialogExtensions._get_active_dialog_context(  # pylint: disable=protected-access
            dialog_context
        )
