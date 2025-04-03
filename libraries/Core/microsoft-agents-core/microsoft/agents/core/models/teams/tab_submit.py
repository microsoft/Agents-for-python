from pydantic import BaseModel
from typing import Optional


class TabSubmit(BaseModel):
    """Initializes a new instance of the TabSubmit class.

    :param tab_entity_context: Gets or sets current tab entity request context.
    :type tab_entity_context: TabEntityContext
    :param context: Gets or sets current user context, i.e., the current theme.
    :type context: TabContext
    :param data: User input data. Free payload containing properties of key-value pairs.
    :type data: TabSubmitData
    """

    tab_entity_context: Optional["TabEntityContext"]
    context: Optional["TabContext"]
    data: Optional["TabSubmitData"]
