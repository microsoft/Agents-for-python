from typing import Optional

from microsoft_agents.activity import MembershipSource, AgentsModel

from .channel_info import ChannelInfo
from .notification_info import NotificationInfo
from .on_behalf_of import OnBehalfOf
from .teams_cahnnel_data_settings import TeamsChannelDataSettings
from .teams_meeting_info import TeamsMeetingInfo
from .tenant_info import TenantInfo
from .team_info import TeamInfo


class TeamsChannelData(AgentsModel):
    channel: Optional[ChannelInfo] = None
    event_type: Optional[str] = None
    team: Optional[TeamInfo] = None
    notification: Optional[NotificationInfo] = None
    tenant: Optional[TenantInfo] = None
    meeting: Optional[TeamsMeetingInfo] = None
    settings: Optional[TeamsChannelDataSettings] = None
    on_behalf_of: Optional[list[OnBehalfOf]] = None
    shared_with_teams: Optional[list[TeamInfo]] = None
    unshared_from_teams: Optional[list[TeamInfo]] = None
    membership_source: Optional[MembershipSource] = None

def parse_teams_channel_data(data: dict) -> TeamsChannelData:
    return TeamsChannelData.model_validate(data)