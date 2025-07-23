# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TabEntityContext(AgentsModel):
    """
    Current TabRequest entity context, or 'tabEntityId'.

    :param tab_entity_id: Gets or sets the entity id of the tab.
    :type tab_entity_id: str
    """

    tab_entity_id: str
