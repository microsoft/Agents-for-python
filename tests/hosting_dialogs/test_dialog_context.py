# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from unittest.mock import MagicMock

from microsoft_agents.hosting.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogSet,
    DialogState,
    DialogTurnStatus,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from microsoft_agents.hosting.core import ConversationState, MemoryStorage
from tests.hosting_dialogs.helpers import DialogTestAdapter


def _make_dc():
    """Create a minimal DialogContext backed by a MagicMock TurnContext."""

    class _Stub(ComponentDialog):
        def __init__(self):
            super().__init__("stub")

    ds = _Stub()._dialogs
    mock_tc = MagicMock()
    return DialogContext(ds, mock_tc, DialogState())


class TestDialogContext:
    def test_null_dialog_set_raises(self):
        with pytest.raises(TypeError):
            DialogContext(None, MagicMock(), DialogState())

    def test_null_turn_context_raises(self):
        dc = _make_dc()
        with pytest.raises(TypeError):
            DialogContext(dc.dialogs, None, DialogState())

    @pytest.mark.asyncio
    async def test_begin_dialog_empty_id_raises(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            with pytest.raises(TypeError):
                await dc.begin_dialog("")

        await adapter.send_text_to_agent_async("hi", callback)

    @pytest.mark.asyncio
    async def test_prompt_empty_id_raises(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            with pytest.raises(TypeError):
                await dc.prompt("", MagicMock())

        await adapter.send_text_to_agent_async("hi", callback)

    @pytest.mark.asyncio
    async def test_prompt_none_options_raises(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            with pytest.raises(TypeError):
                await dc.prompt("somePrompt", None)

        await adapter.send_text_to_agent_async("hi", callback)

    @pytest.mark.asyncio
    async def test_continue_dialog_empty_stack_returns_empty(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        result_holder = {}
        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            result = await dc.continue_dialog()
            result_holder["status"] = result.status

        await adapter.send_text_to_agent_async("hi", callback)
        assert result_holder["status"] == DialogTurnStatus.Empty

    def test_active_dialog_none_on_empty_stack(self):
        dc = _make_dc()
        assert dc.active_dialog is None

    def test_child_none_when_no_active_dialog(self):
        dc = _make_dc()
        assert dc.child is None

    def test_find_dialog_sync_returns_none_for_unknown(self):
        dc = _make_dc()
        assert dc.find_dialog_sync("nonexistent") is None

    @pytest.mark.asyncio
    async def test_cancel_all_dialogs_empty_stack_returns_empty(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        result_holder = {}
        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            result = await dc.cancel_all_dialogs()
            result_holder["status"] = result.status

        await adapter.send_text_to_agent_async("hi", callback)
        assert result_holder["status"] == DialogTurnStatus.Empty

    @pytest.mark.asyncio
    async def test_find_dialog_returns_none_for_unknown(self):
        convo_state = ConversationState(MemoryStorage())
        dialog_state = convo_state.create_property("dialogState")
        ds = DialogSet(dialog_state)

        result_holder = {}
        adapter = DialogTestAdapter()

        async def callback(tc):
            dc = await ds.create_context(tc)
            found = await dc.find_dialog("nonexistent")
            result_holder["found"] = found

        await adapter.send_text_to_agent_async("hi", callback)
        assert result_holder["found"] is None
