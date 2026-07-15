# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dialog_context import DialogContext

from microsoft_agents.hosting.dialogs.memory import scope_path

from .memory_scope import MemoryScope


class ThisMemoryScope(MemoryScope):
    def __init__(self):
        super().__init__(scope_path.THIS)

    def get_memory(self, dialog_context: "DialogContext") -> object:
        if not dialog_context:
            raise TypeError(f"Expecting: DialogContext, but received None")

        return (
            dialog_context.active_dialog.state if dialog_context.active_dialog else None
        )

    def set_memory(self, dialog_context: "DialogContext", memory: object):
        if not dialog_context:
            raise TypeError(f"Expecting: DialogContext, but received None")

        if memory is None:
            raise TypeError(f"Expecting: object, but received None")

        assert dialog_context.active_dialog is not None
        dialog_context.active_dialog.state = memory  # type: ignore[assignment]
