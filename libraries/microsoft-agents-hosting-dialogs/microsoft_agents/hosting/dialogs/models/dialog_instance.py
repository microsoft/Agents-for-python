# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass, field
from typing import Any

@dataclass
class DialogInstance:
    """
    Tracking information for a dialog on the stack.
    """

    id: str | None = None
    state: dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        """
        Gets or sets a stack index.

        :return: Returns stack index.
        :rtype: str
        """
        result = "\ndialog_instance_id: %s\n" % self.id
        if self.state is not None:
            for key, value in self.state.items():
                result += "   {} ({})\n".format(key, str(value))
        return result