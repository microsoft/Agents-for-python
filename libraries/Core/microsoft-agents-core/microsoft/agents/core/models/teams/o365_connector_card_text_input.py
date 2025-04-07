# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import Optional


class O365ConnectorCardTextInput(AgentsModel):
    """O365 connector card text input.

    :param type: Input type name. Default is 'textInput'.
    :type type: str
    :param id: Input Id. It must be unique per entire O365 connector card.
    :type id: str
    :param is_required: Define if this input is a required field. Default value is false.
    :type is_required: Optional[bool]
    :param title: Input title that will be shown as the placeholder
    :type title: Optional[str]
    :param value: Default value for this input field
    :type value: Optional[str]
    :param is_multiline: Define if this input field allows multiple lines of text. Default value is false.
    :type is_multiline: Optional[bool]
    """

    type: str = Field(None, alias="@type")
    id: str = None
    is_required: Optional[bool] = None
    title: Optional[str] = None
    value: Optional[str] = None
    is_multiline: Optional[bool] = None
