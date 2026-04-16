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
