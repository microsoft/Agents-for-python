# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from .tab_entity_context import TabEntityContext
from .tab_context import TabContext


class TabRequest(BaseModel):
    """Invoke ('tab/fetch') request value payload.

    :param tab_entity_context: Gets or sets current tab entity request context.
    :type tab_entity_context: TabEntityContext
    :param context: Gets or sets current tab entity request context.
    :type context: TabContext
    :param state: Gets or sets state, which is the magic code for OAuth Flow.
    :type state: str
    """

    tab_entity_context: TabEntityContext = None
    context: TabContext = None
    state: str = None
