from pydantic import BaseModel
from typing import Optional


class TabRequest(BaseModel):
    """Invoke ('tab/fetch') request value payload.

    :param tab_entity_context: Gets or sets current tab entity request context.
    :type tab_entity_context: Optional["TabEntityContext"]
    :param context: Gets or sets current tab entity request context.
    :type context: Optional["TabContext"]
    :param state: Gets or sets state, which is the magic code for OAuth Flow.
    :type state: Optional[str]
    """

    tab_entity_context: Optional["TabEntityContext"]
    context: Optional["TabContext"]
    state: Optional[str]
