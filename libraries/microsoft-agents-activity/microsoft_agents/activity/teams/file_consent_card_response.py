# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from ..agents_model import AgentsModel


class FileConsentCardResponse(AgentsModel):
    """Represents the value of the invoke activity sent when the user acts on a file consent card.

    :param action: The action the user took. Possible values include: 'accept', 'decline'
    :type action: str | None
    :param context: The context associated with the action.
    :type context: Any | None
    :param upload_info: If the user accepted the file, contains information about the file to be uploaded.
    :type upload_info: Any | None
    """

    action: str | None
    context: Any | None
    upload_info: Any | None
