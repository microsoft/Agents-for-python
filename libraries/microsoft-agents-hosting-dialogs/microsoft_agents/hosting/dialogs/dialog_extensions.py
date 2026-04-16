# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from microsoft_agents.hosting.core import (
    ClaimsIdentity,
    ChannelAdapter,
    StatePropertyAccessor,
    TurnContext,
)
from microsoft_agents.activity import Activity, ActivityTypes, EndOfConversationCodes

from microsoft_agents.hosting.dialogs.memory import DialogStateManager
from .dialog import Dialog
from .dialog_context import DialogContext
from .models import DialogTurnResult
from .models.dialog_events import DialogEvents
from .dialog_set import DialogSet
from .models.dialog_turn_status import DialogTurnStatus


class DialogExtensions:
    @staticmethod
    async def run_dialog(
        dialog: Dialog,
        turn_context: TurnContext,
        accessor: StatePropertyAccessor,
    ):
        """
        Creates a dialog stack and starts a dialog, pushing it onto the stack.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(dialog)

        dialog_context: DialogContext = await dialog_set.create_context(turn_context)

        await DialogExtensions._internal_run(turn_context, dialog.id, dialog_context)

    @staticmethod
    async def _internal_run(
        context: TurnContext, dialog_id: str, dialog_context: DialogContext
    ) -> DialogTurnResult:
        # map TurnState into root dialog context.services
        for key, service in context.turn_state.items():
            dialog_context.services[key] = service

        # get the DialogStateManager configuration
        dialog_state_manager = DialogStateManager(dialog_context)
        await dialog_state_manager.load_all_scopes()
        dialog_context.context.turn_state[dialog_state_manager.__class__.__name__] = (
            dialog_state_manager
        )

        # Loop as long as we are getting valid OnError handled we should continue executing the actions for the turn.
        end_of_turn = False
        dialog_turn_result: DialogTurnResult = DialogTurnResult(DialogTurnStatus.Empty)
        while not end_of_turn:
            try:
                dialog_turn_result = await DialogExtensions.__inner_run(
                    context, dialog_id, dialog_context
                )

                # turn successfully completed, break the loop
                end_of_turn = True
            except Exception as err:
                # fire error event, bubbling from the leaf.
                handled = await dialog_context.emit_event(
                    DialogEvents.error, err, bubble=True, from_leaf=True
                )

                if not handled:
                    # error was NOT handled, throw the exception and end the turn. (This will trigger the
                    # Adapter.OnError handler and end the entire dialog stack)
                    raise

        # save all state scopes to their respective AgentState locations.
        await dialog_state_manager.save_all_changes()

        # return the result
        return dialog_turn_result

    @staticmethod
    async def __inner_run(
        turn_context: TurnContext, dialog_id: str, dialog_context: DialogContext
    ) -> DialogTurnResult:
        # Handle EoC and Reprompt event from a parent bot (can be root bot to skill or skill to skill)
        if DialogExtensions.__is_from_parent_to_skill(turn_context):
            # Handle remote cancellation request from parent.
            if turn_context.activity.type == ActivityTypes.end_of_conversation:
                if not dialog_context.stack:
                    # No dialogs to cancel, just return.
                    return DialogTurnResult(DialogTurnStatus.Empty)

                # Send cancellation message to the dialog to ensure all the parents are canceled
                # in the right order.
                return await dialog_context.cancel_all_dialogs(True)

            # Handle a reprompt event sent from the parent.
            if (
                turn_context.activity.type == ActivityTypes.event
                and turn_context.activity.name == DialogEvents.reprompt_dialog
            ):
                if not dialog_context.stack:
                    # No dialogs to reprompt, just return.
                    return DialogTurnResult(DialogTurnStatus.Empty)

                await dialog_context.reprompt_dialog()
                return DialogTurnResult(DialogTurnStatus.Waiting)

        # Continue or start the dialog.
        result = await dialog_context.continue_dialog()
        if result.status == DialogTurnStatus.Empty:
            result = await dialog_context.begin_dialog(dialog_id)

        await DialogExtensions._send_state_snapshot_trace(dialog_context)

        # Skills should send EoC when the dialog completes.
        if (
            result.status == DialogTurnStatus.Complete
            or result.status == DialogTurnStatus.Cancelled
        ):
            if DialogExtensions.__send_eoc_to_parent(turn_context):
                activity = Activity(  # type: ignore[call-arg]
                    type=ActivityTypes.end_of_conversation,
                    value=result.result,
                    locale=turn_context.activity.locale,
                    code=(
                        EndOfConversationCodes.completed_successfully
                        if result.status == DialogTurnStatus.Complete
                        else EndOfConversationCodes.user_cancelled
                    ),
                )
                await turn_context.send_activity(activity)

        return result

    @staticmethod
    def __is_from_parent_to_skill(turn_context: TurnContext) -> bool:
        """
        Determines if this turn is an incoming request from a parent bot to this skill.
        """
        claims_identity = turn_context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY, None
        )
        return isinstance(claims_identity, ClaimsIdentity) and claims_identity.is_agent_claim()

    @staticmethod
    async def _send_state_snapshot_trace(dialog_context: DialogContext):
        """
        Helper to send a trace activity with a memory snapshot of the active dialog DC.
        """
        claims_identity = dialog_context.context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY, None
        )
        trace_label = (
            "Skill State"
            if isinstance(claims_identity, ClaimsIdentity)
            and claims_identity.is_agent_claim()
            else "Bot State"
        )
        # send trace of memory
        snapshot = DialogExtensions._get_active_dialog_context(
            dialog_context
        ).state.get_memory_snapshot()
        trace_activity = Activity(  # type: ignore[call-arg]
            type=ActivityTypes.trace,
            name="BotState",
            value_type="https://www.botframework.com/schemas/botState",
            value=snapshot,
            label=trace_label,
        )
        await dialog_context.context.send_activity(trace_activity)

    @staticmethod
    def __send_eoc_to_parent(turn_context: TurnContext) -> bool:
        """
        Determines whether to send an EndOfConversation to the parent bot.
        """
        claims_identity = turn_context.turn_state.get(
            ChannelAdapter.AGENT_IDENTITY_KEY, None
        )
        if isinstance(claims_identity, ClaimsIdentity) and claims_identity.is_agent_claim():
            return True

        return False

    @staticmethod
    def _get_active_dialog_context(dialog_context: DialogContext) -> DialogContext:
        """
        Recursively walk up the DC stack to find the active DC.
        """
        child = dialog_context.child
        if not child:
            return dialog_context

        return DialogExtensions._get_active_dialog_context(child)
