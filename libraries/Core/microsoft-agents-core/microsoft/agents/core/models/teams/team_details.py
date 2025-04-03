from pydantic import BaseModel
from typing import Optional


class TeamDetails(BaseModel):
    """Details related to a team.

    :param id: Unique identifier representing a team
    :type id: str
    :param name: Name of team.
    :type name: str
    :param aad_group_id: Azure Active Directory (AAD) Group Id for the team.
    :type aad_group_id: str
    :param channel_count: The count of channels in the team.
    :type channel_count: Optional[int]
    :param member_count: The count of members in the team.
    :type member_count: Optional[int]
    :param type: The team type
    :type type: Optional[str]
    """

    id: str
    name: str
    aad_group_id: str
    channel_count: Optional[int]
    member_count: Optional[int]
    type: Optional[str]
