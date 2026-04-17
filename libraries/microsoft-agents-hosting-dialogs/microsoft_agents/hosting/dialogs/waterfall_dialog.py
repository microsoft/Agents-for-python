# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import uuid
from typing import Callable

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import ActivityTypes

from .models.dialog_reason import DialogReason
from .dialog import Dialog
from .models.dialog_turn_result import DialogTurnResult
from .dialog_context import DialogContext
from .models.dialog_instance import DialogInstance
from .waterfall_step_context import WaterfallStepContext


class WaterfallDialog(Dialog):
    """A dialog composed of a fixed, ordered sequence of steps (a waterfall).

    Each step receives a :class:`WaterfallStepContext` and must either:

    * return :attr:`Dialog.end_of_turn` to wait for user input before proceeding
      to the next step, or
    * call ``await step.next(result)`` / ``await step.begin_dialog(...)`` /
      ``await step.end_dialog(...)`` to advance the flow explicitly.

    Steps are invoked in order.  When the last step completes the dialog ends and
    its result is returned to the parent (if any).  If the waterfall has *no*
    steps at all, ``begin_dialog`` completes immediately with ``None`` as the
    result.

    Telemetry events emitted: ``WaterfallStart``, ``WaterfallStep``,
    ``WaterfallComplete``, and ``WaterfallCancel``.
    """

    PersistedOptions = "options"
    StepIndex = "stepIndex"
    PersistedValues = "values"
    PersistedInstanceId = "instanceId"

    def __init__(self, dialog_id: str, steps: list | None = None):
        """Creates a new WaterfallDialog.

        :param dialog_id: Unique ID for this dialog within its parent DialogSet.
        :param steps: Optional list of async callables (step functions).  Each callable
            must accept a single :class:`WaterfallStepContext` and return a
            :class:`DialogTurnResult`.  Pass ``None`` or omit to start with an empty
            waterfall and add steps later with :meth:`add_step`.
        :raises TypeError: If ``steps`` is not a list.
        """
        super(WaterfallDialog, self).__init__(dialog_id)
        if not steps:
            self._steps = []
        else:
            if not isinstance(steps, list):
                raise TypeError("WaterfallDialog(): steps must be list of steps")
            self._steps = steps

    def add_step(self, step: Callable):
        """
        Adds a new step to the waterfall.
        :param step: Step to add
        :return: Waterfall dialog for fluent calls to `add_step()`.
        """
        if not step:
            raise TypeError("WaterfallDialog.add_step(): step cannot be None.")

        self._steps.append(step)
        return self

    async def begin_dialog(
        self, dialog_context: DialogContext, options: object = None
    ) -> DialogTurnResult:
        """Starts the waterfall from the first step.

        Initialises persisted state (options, values, step index, instance ID) and
        immediately runs step 0.  If the waterfall has no steps the dialog ends at
        once and returns ``None`` to the parent.

        :param dialog_context: The dialog context for the current turn.
        :param options: Optional argument passed through to every step as
            :attr:`WaterfallStepContext.options`.
        :return: The result of the first step, or a Complete result if there are
            no steps.
        """
        if not dialog_context:
            raise TypeError("WaterfallDialog.begin_dialog(): dc cannot be None.")

        # Initialize waterfall state
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state

        instance_id = str(uuid.uuid1())
        state[self.PersistedOptions] = options
        state[self.PersistedValues] = {}
        state[self.PersistedInstanceId] = instance_id

        properties = {}
        properties["DialogId"] = self.id
        properties["InstanceId"] = instance_id
        self.telemetry_client.track_event("WaterfallStart", properties)

        # Run first step
        return await self.run_step(dialog_context, 0, DialogReason.BeginCalled, None)

    async def continue_dialog(  # pylint: disable=unused-argument,arguments-differ
        self,
        dialog_context: DialogContext | None = None,
        reason: DialogReason | None = None,
        result: object = None,
    ) -> DialogTurnResult:
        """Continues the waterfall on the next incoming activity.

        Non-message activities are ignored (returns :attr:`Dialog.end_of_turn`).
        For message activities the user's text is forwarded as the result of the
        previous step via :meth:`resume_dialog`.

        :param dialog_context: The dialog context for the current turn.
        :return: The result of resuming the current step.
        """
        if not dialog_context:
            raise TypeError("WaterfallDialog.continue_dialog(): dc cannot be None.")

        if dialog_context.context.activity.type != ActivityTypes.message:
            return Dialog.end_of_turn

        return await self.resume_dialog(
            dialog_context,
            DialogReason.ContinueCalled,
            dialog_context.context.activity.text,
        )

    async def resume_dialog(
        self, dialog_context: DialogContext, reason: DialogReason, result: object
    ):
        """Advances the waterfall to the next step, passing ``result`` as the previous
        step's output.

        Called automatically by the dialog system when a child dialog completes or
        when :meth:`WaterfallStepContext.next` is called explicitly.

        :param dialog_context: The dialog context for the current turn.
        :param reason: Why the dialog is being resumed.
        :param result: Value returned by the child dialog or previous step.
        :return: The result of running the next step.
        """
        if dialog_context is None:
            raise TypeError("WaterfallDialog.resume_dialog(): dc cannot be None.")

        # Increment step index and run step
        assert dialog_context.active_dialog is not None
        state = dialog_context.active_dialog.state

        return await self.run_step(
            dialog_context, state[self.StepIndex] + 1, reason, result
        )

    async def end_dialog(  # pylint: disable=unused-argument
        self, context: TurnContext, instance: DialogInstance, reason: DialogReason
    ) -> None:
        """Emits telemetry events when the waterfall is cancelled or completes normally.

        :param context: The context for the current turn (unused by this implementation).
        :param instance: The dialog instance being ended.
        :param reason: Why the dialog is ending.
        """
        if reason is DialogReason.CancelCalled:
            index = instance.state[self.StepIndex]
            step_name = self.get_step_name(index)
            instance_id = str(instance.state[self.PersistedInstanceId])
            properties = {
                "DialogId": self.id,
                "StepName": step_name,
                "InstanceId": instance_id,
            }
            self.telemetry_client.track_event("WaterfallCancel", properties)
        else:
            if reason is DialogReason.EndCalled:
                instance_id = str(instance.state[self.PersistedInstanceId])
                properties = {"DialogId": self.id, "InstanceId": instance_id}
                self.telemetry_client.track_event("WaterfallComplete", properties)

        return

    async def on_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Invokes a single waterfall step and emits a ``WaterfallStep`` telemetry event.

        Override this method to add custom logic before or after each step executes.

        :param step_context: Context for the current step.
        :return: The result of the step function.
        """
        step_name = self.get_step_name(step_context.index)
        assert step_context.active_dialog is not None
        instance_id = str(step_context.active_dialog.state[self.PersistedInstanceId])
        properties = {
            "DialogId": self.id,
            "StepName": step_name,
            "InstanceId": instance_id,
        }
        self.telemetry_client.track_event("WaterfallStep", properties)
        result = await self._steps[step_context.index](step_context)
        if result is None:
            raise TypeError(
                f"WaterfallDialog '{self.id}' step '{step_name}' (index {step_context.index}) "
                "returned None. Each step must return 'Dialog.end_of_turn' or a DialogTurnResult."
            )
        return result

    async def run_step(
        self,
        dialog_context: DialogContext,
        index: int,
        reason: DialogReason,
        result: object,
    ) -> DialogTurnResult:
        """Executes a specific step by index, or ends the dialog if the index is past the
        last step.

        Saves the step index into persisted state, constructs a
        :class:`WaterfallStepContext`, and delegates to :meth:`on_step`.

        :param dialog_context: The dialog context for the current turn.
        :param index: Zero-based index of the step to run.
        :param reason: The reason this step is being executed.
        :param result: Value from the previous step or child dialog.
        :return: The step result, or the dialog completion result if all steps are done.
        """
        if not dialog_context:
            raise TypeError(
                "WaterfallDialog.run_steps(): dialog_context cannot be None."
            )
        if index < len(self._steps):
            # Update persisted step index
            assert dialog_context.active_dialog is not None
            state = dialog_context.active_dialog.state
            state[self.StepIndex] = index

            # Create step context
            options = state[self.PersistedOptions]
            values = state[self.PersistedValues]
            step_context = WaterfallStepContext(
                self, dialog_context, options, values, index, reason, result
            )
            return await self.on_step(step_context)

        # End of waterfall so just return any result to parent
        return await dialog_context.end_dialog(result)

    def get_step_name(self, index: int) -> str:
        """Returns a human-readable name for the step at ``index``.

        Uses ``__qualname__`` of the step callable.  Falls back to
        ``"Step{n}of{total}"`` for anonymous lambdas or callables without a
        meaningful qualified name.

        :param index: Zero-based step index.
        :return: A descriptive step name suitable for telemetry.
        """
        step_name = self._steps[index].__qualname__

        if not step_name or step_name.endswith("<lambda>"):
            step_name = f"Step{index + 1}of{len(self._steps)}"

        return step_name
