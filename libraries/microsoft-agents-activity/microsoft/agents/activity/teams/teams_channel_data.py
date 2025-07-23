# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import List
from .channel_info import ChannelInfo
from .team_info import TeamInfo
from .notification_info import NotificationInfo
from .tenant_info import TenantInfo
from .teams_meeting_info import TeamsMeetingInfo
from .teams_channel_data_settings import TeamsChannelDataSettings
from .on_behalf_of import OnBehalfOf


class TeamsChannelData(AgentsModel):
    """Channel data specific to messages received in Microsoft Teams.

    :param channel: Information about the channel in which the message was sent
    :type channel: ChannelInfo
    :param event_type: Type of event.
    :type event_type: str
    :param team: Information about the team in which the message was sent
    :type team: TeamInfo
    :param notification: Notification settings for the message
    :type notification: NotificationInfo
    :param tenant: Information about the tenant in which the message was sent
    :type tenant: TenantInfo
    :param meeting: Information about the meeting in which the message was sent
    :type meeting: TeamsMeetingInfo
    :param settings: Information about the settings in which the message was sent
    :type settings: TeamsChannelDataSettings
    :param on_behalf_of: The OnBehalfOf list for user attribution
    :type on_behalf_of: List[OnBehalfOf]
    """

    channel: ChannelInfo = None
    event_type: str = None
    team: TeamInfo = None
    notification: NotificationInfo = None
    tenant: TenantInfo = None
    meeting: TeamsMeetingInfo = None
    settings: TeamsChannelDataSettings = None
    on_behalf_of: List[OnBehalfOf] = None
