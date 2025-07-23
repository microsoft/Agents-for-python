# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Optional


class O365ConnectorCardViewAction(AgentsModel):
    """O365 connector card ViewAction action.

    :param type: Type of the action. Default is 'ViewAction'.
    :type type: str
    :param name: Name of the ViewAction action.
    :type name: str
    :param id: Id of the ViewAction action.
    :type id: str
    :param target: Target URL for the ViewAction action.
    :type target: Optional[str]
    """

    type: str = Field(None, alias="@type")
    name: str = None
    id: str = Field(None, alias="@id")
    target: Optional[str] = None
