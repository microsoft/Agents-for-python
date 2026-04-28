# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import AsyncMock, MagicMock

from microsoft_agents.hosting.dialogs import (
    Dialog,
    DialogTurnResult,
    DialogTurnStatus,
    DialogReason,
)


class _ConcreteDialog(Dialog):
    """Minimal concrete Dialog for testing base class behavior."""

    async def begin_dialog(self, dialog_context, options=None):
        return DialogTurnResult(DialogTurnStatus.Complete)


class TestDialog:
    def test_null_id_raises(self):
        with pytest.raises((TypeError, Exception)):
            _ConcreteDialog(None)

    def test_blank_id_raises(self):
        with pytest.raises((TypeError, Exception)):
            _ConcreteDialog("   ")

    def test_telemetry_client_defaults_non_none(self):
        dialog = _ConcreteDialog("A")
        assert dialog.telemetry_client is not None

    def test_get_version_returns_id(self):
        dialog = _ConcreteDialog("my-dialog")
        assert dialog.get_version() == "my-dialog"

    def test_id_property(self):
        dialog = _ConcreteDialog("test-id")
        assert dialog.id == "test-id"

    @pytest.mark.asyncio
    async def test_continue_dialog_calls_end_dialog(self):
        """Default continue_dialog calls end_dialog(None) → Complete."""
        dialog = _ConcreteDialog("A")
        dc = MagicMock()
        dc.end_dialog = AsyncMock(
            return_value=DialogTurnResult(DialogTurnStatus.Complete)
        )

        result = await dialog.continue_dialog(dc)

        assert result.status == DialogTurnStatus.Complete
        dc.end_dialog.assert_awaited_once_with(None)

    @pytest.mark.asyncio
    async def test_resume_dialog_calls_end_dialog_with_result(self):
        """Default resume_dialog calls end_dialog(result) → Complete."""
        dialog = _ConcreteDialog("A")
        dc = MagicMock()
        dc.end_dialog = AsyncMock(
            return_value=DialogTurnResult(DialogTurnStatus.Complete, "done")
        )

        result = await dialog.resume_dialog(dc, DialogReason.BeginCalled, "done")

        assert result.status == DialogTurnStatus.Complete
        dc.end_dialog.assert_awaited_once_with("done")

    @pytest.mark.asyncio
    async def test_reprompt_dialog_is_noop(self):
        """Default reprompt_dialog is a no-op (no exception)."""
        dialog = _ConcreteDialog("A")
        await dialog.reprompt_dialog(MagicMock(), MagicMock())

    @pytest.mark.asyncio
    async def test_end_dialog_is_noop(self):
        """Default end_dialog is a no-op (no exception)."""
        dialog = _ConcreteDialog("A")
        await dialog.end_dialog(MagicMock(), MagicMock(), DialogReason.EndCalled)
