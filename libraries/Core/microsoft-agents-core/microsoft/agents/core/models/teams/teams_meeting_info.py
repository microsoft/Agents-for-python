# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class TeamsMeetingInfo(BaseModel):
    """Describes a Teams Meeting.

    :param id: Unique identifier representing a meeting
    :type id: str
    """

    id: str = None
