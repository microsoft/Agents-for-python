# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TeamInfo(AgentsModel):
    """Describes a team.

    :param id: Unique identifier representing a team
    :type id: str
    :param name: Name of team.
    :type name: str
    :param aad_group_id: Azure AD Teams group ID.
    :type aad_group_id: str
    """

    id: str = None
    name: str = None
    aad_group_id: str = None
