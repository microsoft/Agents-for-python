# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .dialog_context import DialogContext
from .models.dialog_reason import DialogReason
from .models.dialog_turn_result import DialogTurnResult
from .dialog_state import DialogState


class WaterfallStepContext(DialogContext):
    """Context passed to each step function in a :class:`microsoft_agents.hosting.dialogs.WaterfallDialog`.

    Inherits from :class:`microsoft_agents.hosting.dialogs.DialogContext` so step functions can call
    :meth:`microsoft_agents.hosting.dialogs.DialogContext.begin_dialog`, :meth:`microsoft_agents.hosting.dialogs.DialogContext.prompt`, :meth:`microsoft_agents.hosting.dialogs.DialogContext.end_dialog`, etc. directly on
    the step context.

    In addition to the standard :class:`microsoft_agents.hosting.dialogs.DialogContext` interface, a step context
    provides read-only properties for the current step index, the options passed
    to the waterfall, the reason this step is executing, the result from the
    previous step (or child dialog), and a shared ``values`` dict that persists
    across all steps of the same waterfall instance.

    Call :meth:`microsoft_agents.hosting.dialogs.WaterfallStepContext.next` to skip ahead to the next step without waiting for user
    input.  Calling :meth:`microsoft_agents.hosting.dialogs.WaterfallStepContext.next` more than once in the same step raises an
    exception.
    """

    def __init__(
        self,
        parent,
        dc: DialogContext,
        options: object,
        values: dict[str, object],
        index: int,
        reason: DialogReason,
        result: object = None,
    ):
        super(WaterfallStepContext, self).__init__(
            dc.dialogs, dc.context, DialogState(dc.stack)
        )
        self._wf_parent = parent
        self._next_called = False
        self._index = index
        self._options = options
        self._reason = reason
        self._result = result
        self._values = values
        self.parent = dc.parent

    @property
    def index(self) -> int:
        """Zero-based index of the currently executing step."""
        return self._index

    @property
    def options(self) -> object:
        """Options originally passed to :meth:`microsoft_agents.hosting.dialogs.WaterfallDialog.begin_dialog`.
        Shared across all steps of the same waterfall run.
        """
        return self._options

    @property
    def reason(self) -> DialogReason:
        """Why this step is executing (e.g. ``BeginCalled``, ``ContinueCalled``,
        ``NextCalled``).
        """
        return self._reason

    @property
    def result(self) -> object:
        """The value returned by the previous step or a child dialog that was
        started from the previous step.  ``None`` for the first step.
        """
        return self._result

    @property
    def values(self) -> dict[str, object]:
        """A dictionary that persists across every step of the same waterfall
        instance.  Use it to accumulate data collected across multiple steps.

        .. note::
            Values stored here are scoped to the current waterfall run only and
            are lost when the waterfall ends.
        """
        return self._values

    async def next(self, result: object) -> DialogTurnResult:
        """Skips to the next step of the waterfall, passing ``result`` as the
        previous step's output.

        This is useful when a step wants to bypass waiting for user input and
        advance immediately (e.g. when data was already available).

        :param result: Value to pass to the next step as
            :attr:`microsoft_agents.hosting.dialogs.WaterfallStepContext.result`.
        :raises Exception: If called more than once within the same step.
        :return: The result of running the next step.
        """
        if self._next_called is True:
            raise Exception(
                "WaterfallStepContext.next(): method already called for dialog and step '%s'[%s]."
                % (self._wf_parent.id, self._index)
            )

        # Trigger next step
        self._next_called = True
        return await self._wf_parent.resume_dialog(
            self, DialogReason.NextCalled, result
        )
