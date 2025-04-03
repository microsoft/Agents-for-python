from pydantic import BaseModel
from typing import List


class MeetingNotificationChannelData(BaseModel):
    """Specify Teams Bot meeting notification channel data.

    :param on_behalf_of_list: The Teams Bot meeting notification's OnBehalfOf list.
    :type on_behalf_of_list: list[OnBehalfOf]
    """

    on_behalf_of_list: List["OnBehalfOf"]
