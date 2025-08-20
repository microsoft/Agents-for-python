# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Annotated, Optional


class MessageActionsPayloadApp(AgentsModel):
    """Represents an application entity.

    :param application_identity_type: The type of application. Possible values include: 'aadApplication', 'bot', 'tenantBot', 'office365Connector', 'webhook'
    :type application_identity_type: Optional[str]
    :param id: The id of the application.
    :type id: Optional[str]
    :param display_name: The plaintext display name of the application.
    :type display_name: Optional[str]
    """

    application_identity_type: Optional[
        Annotated[
            str,
            Field(
                pattern=r"^(aadApplication|bot|tenantBot|office365Connector|webhook)$"
            ),
        ]
    ]
    id: Optional[str]
    display_name: Optional[str]
