# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field

from .models.dialog_instance import DialogInstance


@dataclass
class DialogState:
    """
    Contains state information for the dialog stack.
    """

    dialog_stack: list[DialogInstance] = field(default_factory=list)

    def __str__(self):
        if not self.dialog_stack:
            return "dialog stack empty!"
        return " ".join(map(str, self.dialog_stack))
