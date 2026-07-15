# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogReason,
    DialogSet,
    DialogState,
    DialogTurnResult,
    DialogTurnStatus,
    WaterfallDialog,
)
from microsoft_agents.hosting.dialogs.waterfall_step_context import WaterfallStepContext


def _make_step_context():
    """Create a WaterfallStepContext backed by mock objects."""

    class _Stub(ComponentDialog):
        def __init__(self):
            super().__init__("stub")

    ds = _Stub()._dialogs
    mock_tc = MagicMock()
    dc = DialogContext(ds, mock_tc, DialogState())

    wf_dialog = WaterfallDialog("wf", [])
    wf_dialog.resume_dialog = AsyncMock(
        return_value=DialogTurnResult(DialogTurnStatus.Complete)
    )

    return WaterfallStepContext(wf_dialog, dc, None, {}, 0, DialogReason.BeginCalled)


class TestWaterfallStepContext:
    @pytest.mark.asyncio
    async def test_next_called_twice_raises(self):
        """Calling next() a second time on the same step context must raise."""
        step_ctx = _make_step_context()

        # First call succeeds
        await step_ctx.next(None)

        # Second call raises
        with pytest.raises(Exception, match="already called"):
            await step_ctx.next(None)

    @pytest.mark.asyncio
    async def test_next_calls_resume_on_parent_dialog(self):
        """next() delegates to the parent WaterfallDialog's resume_dialog."""
        step_ctx = _make_step_context()
        await step_ctx.next("my-result")
        step_ctx._wf_parent.resume_dialog.assert_awaited_once()

    def test_step_context_properties(self):
        """WaterfallStepContext exposes index, options, reason, result, values."""
        step_ctx = _make_step_context()
        assert step_ctx.index == 0
        assert step_ctx.options is None
        assert step_ctx.reason == DialogReason.BeginCalled
        assert step_ctx.result is None
        assert step_ctx.values == {}

    def test_step_context_with_result(self):
        class _Stub(ComponentDialog):
            def __init__(self):
                super().__init__("stub")

        ds = _Stub()._dialogs
        dc = DialogContext(ds, MagicMock(), DialogState())
        wf = WaterfallDialog("wf", [])
        wf.resume_dialog = AsyncMock(
            return_value=DialogTurnResult(DialogTurnStatus.Complete)
        )

        step_ctx = WaterfallStepContext(
            wf,
            dc,
            {"key": "val"},
            {"v": 1},
            2,
            DialogReason.NextCalled,
            "previous-result",
        )

        assert step_ctx.index == 2
        assert step_ctx.options == {"key": "val"}
        assert step_ctx.values == {"v": 1}
        assert step_ctx.result == "previous-result"
        assert step_ctx.reason == DialogReason.NextCalled
