# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Annotated

from pydantic import Field
from ..agents_model import AgentsModel


class MessageActionsPayloadApp(AgentsModel):
    """Represents an application entity.

    :param application_identity_type: The type of application. Possible values include: 'aadApplication', 'bot', 'tenantBot', 'office365Connector', 'webhook'
    :type application_identity_type: str | None
    :param id: The id of the application.
    :type id: str | None
    :param display_name: The plaintext display name of the application.
    :type display_name: str | None
    """

    application_identity_type: (
        Annotated[
            str,
            Field(
                pattern=r"^(aadApplication|bot|tenantBot|office365Connector|webhook)$"
            ),
        ]
        | None
    )
    id: str | None
    display_name: str | None
