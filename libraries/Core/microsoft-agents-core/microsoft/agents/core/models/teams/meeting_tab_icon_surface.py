from pydantic import BaseModel


class MeetingTabIconSurface(BaseModel):
    """Specifies meeting tab icon surface.

    :param tab_entity_id: The tab entity Id of this MeetingTabIconSurface.
    :type tab_entity_id: str
    """

    tab_entity_id: str
