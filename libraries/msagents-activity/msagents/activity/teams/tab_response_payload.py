# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel

from .tab_response_cards import TabResponseCards
from .tab_suggested_actions import TabSuggestedActions


class TabResponsePayload(AgentsModel):
    """Initializes a new instance of the TabResponsePayload class.

    :param type: Gets or sets choice of action options when responding to the
     tab/fetch message. Possible values include: 'continue', 'auth' or 'silentAuth'
    :type type: str
    :param value: Gets or sets the TabResponseCards when responding to
     tab/fetch activity with type of 'continue'.
    :type value: TabResponseCards
    :param suggested_actions: Gets or sets the Suggested Actions for this card tab.
    :type suggested_actions: TabSuggestedActions
    """

    type: str = None
    value: TabResponseCards = None
    suggested_actions: TabSuggestedActions = None
