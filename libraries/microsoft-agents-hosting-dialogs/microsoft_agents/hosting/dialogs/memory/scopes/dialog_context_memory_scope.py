# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...dialog_context import DialogContext

from microsoft_agents.hosting.dialogs.memory import scope_path

from .memory_scope import MemoryScope


class DialogContextMemoryScope(MemoryScope):
    def __init__(self):
        # pylint: disable=invalid-name
        super().__init__(scope_path.DIALOG_CONTEXT, include_in_snapshot=False)
        # Stack name.
        self.STACK = "stack"

        # Active dialog name.
        self.ACTIVE_DIALOG = "activeDialog"

        # Parent name.
        self.PARENT = "parent"

    def get_memory(self, dialog_context: "DialogContext") -> object:
        """
        Gets the backing memory for this scope.
        """
        if not dialog_context:
            raise TypeError(f"Expecting: DialogContext, but received None")

        memory = {}
        stack = list([])
        current_dc = dialog_context

        # go to leaf node
        while current_dc.child:
            current_dc = current_dc.child

        while current_dc:
            # (PORTERS NOTE: javascript stack is reversed with top of stack on end)
            for item in current_dc.stack:
                # filter out ActionScope items because they are internal bookkeeping.
                if not item.id.startswith("ActionScope["):
                    stack.append(item.id)

            current_dc = current_dc.parent

        # top of stack is stack[0].
        memory[self.STACK] = stack
        memory[self.ACTIVE_DIALOG] = (
            dialog_context.active_dialog.id if dialog_context.active_dialog else None
        )
        memory[self.PARENT] = (
            dialog_context.parent.active_dialog.id
            if dialog_context.parent and dialog_context.parent.active_dialog
            else None
        )
        return memory

    def set_memory(self, dialog_context: "DialogContext", memory: object):
        raise Exception(
            f"{self.__class__.__name__}.set_memory not supported (read only)"
        )
