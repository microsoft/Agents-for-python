# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class MeetingDetails(AgentsModel):
    """Specific details of a Teams meeting.

    :param ms_graph_resource_id: The MsGraphResourceId, used specifically for MS Graph API calls.
    :type ms_graph_resource_id: str
    :param scheduled_start_time: The meeting's scheduled start time, in UTC.
    :type scheduled_start_time: str
    :param scheduled_end_time: The meeting's scheduled end time, in UTC.
    :type scheduled_end_time: str
    :param type: The meeting's type.
    :type type: str
    """

    ms_graph_resource_id: str = None
    scheduled_start_time: str = None
    scheduled_end_time: str = None
    type: str = None
