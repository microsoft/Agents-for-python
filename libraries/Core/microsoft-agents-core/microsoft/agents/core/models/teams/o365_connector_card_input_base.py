from pydantic import BaseModel
from typing import Optional


class O365ConnectorCardInputBase(BaseModel):
    """Base class for O365 connector card inputs.

    :param type: Input type name. Possible values include: 'textInput', 'dateInput', 'multichoiceInput'
    :type type: str
    :param id: Input Id. It must be unique per entire O365 connector card.
    :type id: str
    :param is_required: Define if this input is a required field. Default value is false.
    :type is_required: Optional[bool]
    :param title: Input title that will be shown as the placeholder
    :type title: Optional[str]
    :param value: Default value for this input field
    :type value: Optional[str]
    """

    type: str
    id: str
    is_required: Optional[bool]
    title: Optional[str]
    value: Optional[str]
