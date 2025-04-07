# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import Field
from pydantic import BaseModel
from typing import List
from .o365_connector_card_open_uri_target import O365ConnectorCardOpenUriTarget


class O365ConnectorCardOpenUri(BaseModel):
    """O365 connector card OpenUri action.

    :param type: Type of the action. Default is 'OpenUri'.
    :type type: str
    :param name: Name of the OpenUri action.
    :type name: str
    :param id: Id of the OpenUri action.
    :type id: str
    :param targets: List of targets for the OpenUri action.
    :type targets: List["O365ConnectorCardOpenUriTarget"]
    """

    type: str = Field(None, alias="@type")
    name: str = None
    id: str = Field(None, alias="@id")
    targets: List[O365ConnectorCardOpenUriTarget] = None
