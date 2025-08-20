# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Any, Optional


class FileConsentCardResponse(AgentsModel):
    """Represents the value of the invoke activity sent when the user acts on a file consent card.

    :param action: The action the user took. Possible values include: 'accept', 'decline'
    :type action: Optional[str]
    :param context: The context associated with the action.
    :type context: Optional[Any]
    :param upload_info: If the user accepted the file, contains information about the file to be uploaded.
    :type upload_info: Optional[Any]
    """

    action: Optional[str]
    context: Optional[Any]
    upload_info: Optional[Any]
