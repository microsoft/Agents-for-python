# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class TeamsMeetingInfo(AgentsModel):
    """Describes a Teams Meeting.

    :param id: Unique identifier representing a meeting
    :type id: str
    """

    id: str = None
