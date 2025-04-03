from pydantic import BaseModel


class TabEntityContext(BaseModel):
    """
    Current TabRequest entity context, or 'tabEntityId'.

    :param tab_entity_id: Gets or sets the entity id of the tab.
    :type tab_entity_id: str
    """

    tab_entity_id: str
