# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TaskModuleMessageResponse(AgentsModel):
    """Response to display a message in a task module.

    :param type: The type of response. Default is 'message'.
    :type type: str
    :param value: The message to display.
    :type value: str | None
    """

    type: str = None
    value: str | None = None
