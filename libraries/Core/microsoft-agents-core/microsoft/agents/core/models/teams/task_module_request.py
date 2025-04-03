from pydantic import BaseModel
from typing import Any, Optional


class TaskModuleRequest(BaseModel):
    """Task module invoke request value payload.

    :param data: User input data. Free payload with key-value pairs.
    :type data: object
    :param context: Current user context, i.e., the current theme
    :type context: Optional[Any]
    :param tab_entity_context: Gets or sets current tab request context.
    :type tab_entity_context: Optional[TabEntityContext]
    """

    data: Optional[Any]
    context: Optional[Any]
    tab_entity_context: Optional["TabEntityContext"]
