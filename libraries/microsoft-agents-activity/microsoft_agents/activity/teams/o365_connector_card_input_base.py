# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel


class O365ConnectorCardInputBase(AgentsModel):
    """Base class for O365 connector card inputs.

    :param type: Input type name. Possible values include: 'textInput', 'dateInput', 'multichoiceInput'
    :type type: str
    :param id: Input Id. It must be unique per entire O365 connector card.
    :type id: str
    :param is_required: Define if this input is a required field. Default value is false.
    :type is_required: bool | None
    :param title: Input title that will be shown as the placeholder
    :type title: str | None
    :param value: Default value for this input field
    :type value: str | None
    """

    type: str = Field(None, alias="@type")
    id: str = None
    is_required: bool | None = None
    title: str | None = None
    value: str | None = None
