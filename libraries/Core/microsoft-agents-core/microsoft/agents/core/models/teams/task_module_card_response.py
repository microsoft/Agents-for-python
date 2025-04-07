# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from .tab_response import TabResponse


class TaskModuleCardResponse(BaseModel):
    """Tab Response to 'task/submit' from a tab.

    :param value: The JSON for the Adaptive cards to appear in the tab.
    :type value: TabResponse
    """

    value: TabResponse = None
