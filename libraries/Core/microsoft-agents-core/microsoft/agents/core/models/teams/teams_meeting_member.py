from pydantic import BaseModel


class TeamsMeetingMember(BaseModel):
    """Data about the meeting participants.

    :param user: The channel user data.
    :type user: TeamsChannelAccount
    :param meeting: The user meeting details.
    :type meeting: UserMeetingDetails
    """

    user: "TeamsChannelAccount"
    meeting: "UserMeetingDetails"
