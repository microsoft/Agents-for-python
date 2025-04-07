# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel


class O365ConnectorCardActionBase(AgentsModel):
    """O365 connector card action base.

    :param type: Type of the action. Possible values include: 'ViewAction', 'OpenUri', 'HttpPOST', 'ActionCard'
    :type type: str
    :param name: Name of the action that will be used as button title
    :type name: str
    :param id: Action Id
    :type id: str
    """

    type: str = Field(None, alias="@type")
    name: str = None
    id: str = Field(None, alias="@id")
