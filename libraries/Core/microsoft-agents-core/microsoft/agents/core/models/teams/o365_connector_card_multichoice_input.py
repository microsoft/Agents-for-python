from pydantic import BaseModel
from typing import List, Optional


class O365ConnectorCardMultichoiceInput(BaseModel):
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

    type: str = "multichoiceInput"
    id: str
    is_required: Optional[bool]
    title: Optional[str]
    value: Optional[str]
    choices: List["O365ConnectorCardMultichoiceInputChoice"]
    style: Optional[str]
    is_multi_select: Optional[bool]
