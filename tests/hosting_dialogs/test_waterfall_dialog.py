# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import MagicMock

from microsoft_agents.activity import ActivityTypes
from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    Dialog,
    DialogContext,
    DialogReason,
    DialogSet,
    DialogState,
    DialogTurnResult,
    DialogTurnStatus,
    WaterfallDialog,
)


def _make_dc(activity_type="message"):
    """Create a minimal DialogContext with the given activity type."""

    class _Stub(ComponentDialog):
        def __init__(self):
            super().__init__("stub")

    ds = _Stub()._dialogs
    mock_tc = MagicMock()
    mock_tc.activity.type = activity_type
    return DialogContext(ds, mock_tc, DialogState())


class TestWaterfallDialogValidation:
    @pytest.mark.asyncio
    async def test_begin_dialog_null_dc_raises(self):
        dialog = WaterfallDialog("A", [])
        with pytest.raises((TypeError, Exception)):
            await dialog.begin_dialog(None)

    @pytest.mark.asyncio
    async def test_continue_dialog_null_dc_raises(self):
        dialog = WaterfallDialog("A", [])
        with pytest.raises((TypeError, Exception)):
            await dialog.continue_dialog(None)

    @pytest.mark.asyncio
    async def test_continue_dialog_returns_waiting_for_non_message_activity(self):
        """WaterfallDialog.continue_dialog returns end_of_turn for non-message activities."""
        dialog = WaterfallDialog("A", [])
        dc = _make_dc(activity_type=ActivityTypes.event)

        result = await dialog.continue_dialog(dc)

        # end_of_turn is DialogTurnResult(Waiting)
        assert result.status == DialogTurnStatus.Waiting

    @pytest.mark.asyncio
    async def test_resume_dialog_null_dc_raises(self):
        dialog = WaterfallDialog("A", [])
        with pytest.raises((TypeError, Exception)):
            await dialog.resume_dialog(None, DialogReason.BeginCalled, "result")

    @pytest.mark.asyncio
    async def test_run_step_null_dc_raises(self):
        dialog = WaterfallDialog("A", [])
        with pytest.raises((TypeError, Exception)):
            await dialog.run_step(None, 0, DialogReason.BeginCalled, None)

    def test_none_name_raises(self):
        with pytest.raises((TypeError, Exception)):
            WaterfallDialog(None, [])

    def test_add_none_step_raises(self):
        dialog = WaterfallDialog("A", [])
        with pytest.raises((TypeError, Exception)):
            dialog.add_step(None)

    def test_steps_must_be_list(self):
        with pytest.raises((TypeError, Exception)):
            WaterfallDialog("A", {1, 2})

    @pytest.mark.asyncio
    async def test_empty_steps_completes_immediately(self):
        """WaterfallDialog with no steps ends immediately with None result."""
        from microsoft_agents.hosting.core import ConversationState, MemoryStorage
        from microsoft_agents.hosting.dialogs import DialogSet
        from tests.hosting_dialogs.helpers import DialogTestAdapter

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        dialogs = DialogSet(dialog_state)
        dialogs.add(WaterfallDialog("empty-waterfall", []))

        result_holder = {}

        async def exec(tc):
            dc = await dialogs.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                results = await dc.begin_dialog("empty-waterfall")
            result_holder["status"] = results.status
            result_holder["result"] = results.result
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        await adapter.send("hi")
        assert result_holder["status"] == DialogTurnStatus.Complete
        assert result_holder["result"] is None

    @pytest.mark.asyncio
    async def test_continue_dialog_non_message_returns_waiting(self):
        """WaterfallDialog.continue_dialog ignores non-message activities."""
        dialog = WaterfallDialog("A", [lambda step: Dialog.end_of_turn])
        dc = _make_dc(activity_type=ActivityTypes.event)
        result = await dialog.continue_dialog(dc)
        assert result.status == DialogTurnStatus.Waiting


class TestWaterfallStepName:
    def test_get_step_name_named_function_uses_qualname(self):
        """Named step functions expose their __qualname__ as the step name."""

        async def my_named_step(step):
            return Dialog.end_of_turn

        dialog = WaterfallDialog("A", [my_named_step])
        assert "my_named_step" in dialog.get_step_name(0)

    def test_get_step_name_lambda_uses_fallback_format(self):
        """Lambda steps fall back to 'Step{n}of{total}' because their __qualname__ ends in '<lambda>'."""
        dialog = WaterfallDialog("A", [lambda s: None, lambda s: None])
        assert dialog.get_step_name(0) == "Step1of2"
        assert dialog.get_step_name(1) == "Step2of2"


class TestWaterfallStepNoneReturn:
    @pytest.mark.asyncio
    async def test_step_returning_none_raises_type_error(self):
        """A step returning None raises a clear TypeError instead of a confusing AttributeError."""
        from microsoft_agents.hosting.core import ConversationState, MemoryStorage
        from microsoft_agents.hosting.dialogs import DialogSet
        from tests.hosting_dialogs.helpers import DialogTestAdapter

        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        async def bad_step(step):
            return None  # programmer forgot to return Dialog.end_of_turn

        ds.add(WaterfallDialog("bad-waterfall", [bad_step]))

        error_holder = {}

        async def exec(tc):
            dc = await ds.create_context(tc)
            results = await dc.continue_dialog()
            if results.status == DialogTurnStatus.Empty:
                try:
                    await dc.begin_dialog("bad-waterfall")
                except TypeError as e:
                    error_holder["error"] = e
            await convo_state.save(tc)

        adapter = DialogTestAdapter(exec)
        await adapter.send("hi")

        assert "error" in error_holder, "Expected TypeError but none was raised"
        error_msg = str(error_holder["error"]).lower()
        assert "none" in error_msg or "step" in error_msg
