# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TaskModuleRequestContext(AgentsModel):
    """Context for a task module request.

    :param theme: The current user's theme.
    :type theme: str | None
    """

    theme: str | None = None
