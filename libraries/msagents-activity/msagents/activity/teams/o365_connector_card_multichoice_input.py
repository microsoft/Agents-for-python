# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import Field
from ..agents_model import AgentsModel
from typing import List, Optional
from .o365_connector_card_multichoice_input_choice import (
    O365ConnectorCardMultichoiceInputChoice,
)


class O365ConnectorCardMultichoiceInput(AgentsModel):
    """O365 connector card multichoice input.

    :param type: Input type name. Default is 'multichoiceInput'.
    :type type: str
    :param id: Input Id. It must be unique per entire O365 connector card.
    :type id: str
    :param is_required: Define if this input is a required field. Default value is false.
    :type is_required: Optional[bool]
    :param title: Input title that will be shown as the placeholder
    :type title: Optional[str]
    :param value: Default value for this input field
    :type value: Optional[str]
    :param choices: Set of choices for this input field.
    :type choices: List["O365ConnectorCardMultichoiceInputChoice"]
    :param style: Choice style. Possible values include: 'compact', 'expanded'
    :type style: Optional[str]
    :param is_multi_select: Define if this input field allows multiple selections. Default value is false.
    :type is_multi_select: Optional[bool]
    """

    type: str = Field(None, alias="@type")
    id: str = None
    is_required: Optional[bool] = None
    title: Optional[str] = None
    value: Optional[str] = None
    choices: List[O365ConnectorCardMultichoiceInputChoice] = None
    style: Optional[str] = None
    is_multi_select: Optional[bool] = None
