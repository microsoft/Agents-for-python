from pydantic import BaseModel
from typing import Any, Optional


class FileConsentCardResponse(BaseModel):
    """Represents the value of the invoke activity sent when the user acts on a file consent card.

    :param action: The action the user took. Possible values include: 'accept', 'decline'
    :type action: str
    :param context: The context associated with the action.
    :type context: Any
    :param upload_info: If the user accepted the file, contains information about the file to be uploaded.
    :type upload_info: Optional[Any]
    """

    action: str
    context: Any
    upload_info: Optional[Any]
