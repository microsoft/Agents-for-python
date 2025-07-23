# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Optional


class O365ConnectorCardHttpPOST(AgentsModel):
    """O365 connector card HttpPOST action.

    :param type: Type of the action. Default is 'HttpPOST'.
    :type type: str
    :param name: Name of the HttpPOST action.
    :type name: str
    :param id: Id of the HttpPOST action.
    :type id: str
    :param body: Content of the HttpPOST action.
    :type body: Optional[str]
    """

    type: str = Field(None, alias="@type")
    name: str = None
    id: str = Field(None, alias="@id")
    body: Optional[str] = None
