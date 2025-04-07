# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class TeamDetails(BaseModel):
    """Details related to a team.

    :param id: Unique identifier representing a team
    :type id: str
    :param name: Name of team.
    :type name: str
    :param aad_group_id: Azure Active Directory (AAD) Group Id for the team.
    :type aad_group_id: str
    :param channel_count: The count of channels in the team.
    :type channel_count: int
    :param member_count: The count of members in the team.
    :type member_count: int
    :param type: The team type
    :type type: str
    """

    id: str = None
    name: str = None
    aad_group_id: str = None
    channel_count: int = None
    member_count: int = None
    type: str = None
