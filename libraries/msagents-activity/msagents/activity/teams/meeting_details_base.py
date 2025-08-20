# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel


class MeetingDetailsBase(AgentsModel):
    """Specific details of a Teams meeting.

    :param id: The meeting's Id, encoded as a BASE64 string.
    :type id: str
    :param join_url: The URL used to join the meeting.
    :type join_url: str
    :param title: The title of the meeting.
    :type title: str
    """

    id: str = Field(None, alias="uniqueId")
    join_url: str = None
    title: str = None
