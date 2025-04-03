from pydantic import BaseModel


class TeamInfo(BaseModel):
    """Describes a team.

    :param id: Unique identifier representing a team
    :type id: str
    :param name: Name of team.
    :type name: str
    :param aad_group_id: Azure AD Teams group ID.
    :type aad_group_id: str
    """

    id: str
    name: str
    aad_group_id: str
