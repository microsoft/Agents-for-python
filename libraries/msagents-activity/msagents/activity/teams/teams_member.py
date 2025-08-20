# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TeamsMember(AgentsModel):
    """Describes a member.

    :param id: Unique identifier representing a member (user or channel).
    :type id: str
    """

    id: str = None
