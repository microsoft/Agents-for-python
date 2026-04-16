# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import TYPE_CHECKING

from .dialog import Dialog

if TYPE_CHECKING:
    from .dialog_context import DialogContext


class DialogContainer(Dialog):
    """
    A Dialog that is composed of other dialogs.
    This is the abstract base class for dialogs that contain child dialogs (e.g. ComponentDialog).
    """

    def __init__(self, dialog_id: str | None = None):
        super().__init__(dialog_id or self.__class__.__name__)
        # Import here to avoid circular imports at module level
        from .dialog_set import DialogSet  # pylint: disable=import-outside-toplevel
        self.dialogs = DialogSet(None)

    def create_child_context(self, dialog_context: DialogContext) -> DialogContext:
        """
        Creates the inner dialog context for the active child dialog, if there is one.
        :param dialog_context: The parent dialog context.
        :return: The child dialog context, or None if there is no active child.
        """
        raise NotImplementedError(
            "DialogContainer.create_child_context(): not implemented."
        )
