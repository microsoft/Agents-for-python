# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .dialog import Dialog
from .dialog_set import DialogSet

if TYPE_CHECKING:
    from .dialog_context import DialogContext


class DialogContainer(Dialog, ABC):

    def __init__(self, dialog_id: str):
        super().__init__(dialog_id)
        self.dialogs = DialogSet()

    @abstractmethod
    def create_child_context(self, dialog_context: DialogContext) -> DialogContext:
        """
        Creates the inner dialog context for the active child dialog, if there is one.
        :param dialog_context: The parent dialog context.
        :return: The child dialog context, or None if there is no active child.
        """
        raise NotImplementedError(
            "DialogContainer.create_child_context(): not implemented."
        )
