from pydantic import BaseModel


class UserMeetingDetails(BaseModel):
    """Specific details of a user in a Teams meeting.

    :param role: Role of the participant in the current meeting.
    :type role: str
    :param in_meeting: True, if the participant is in the meeting.
    :type in_meeting: bool
    """

    role: str
    in_meeting: bool
