# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from .tab_entity_context import TabEntityContext
from .tab_context import TabContext
from .tab_submit_data import TabSubmitData


class TabSubmit(AgentsModel):
    """Initializes a new instance of the TabSubmit class.

    :param tab_entity_context: Gets or sets current tab entity request context.
    :type tab_entity_context: TabEntityContext
    :param context: Gets or sets current user context, i.e., the current theme.
    :type context: TabContext
    :param data: User input data. Free payload containing properties of key-value pairs.
    :type data: TabSubmitData
    """

    tab_entity_context: TabEntityContext = None
    context: TabContext = None
    data: TabSubmitData = None
