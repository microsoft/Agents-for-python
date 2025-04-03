from pydantic import BaseModel


class O365ConnectorCardDateInput(BaseModel):
    """O365 connector card date input.

    :param type: Input type name. Possible values include: 'textInput', 'dateInput', 'multichoiceInput'
    :type type: str
    :param id: Input Id. It must be unique per entire O365 connector card.
    :type id: str
    :param is_required: Define if this input is a required field. Default value is false.
    :type is_required: bool
    :param title: Input title that will be shown as the placeholder
    :type title: str
    :param value: Default value for this input field
    :type value: str
    :param include_time: Include time input field. Default value is false (date only).
    :type include_time: bool
    """

    type: str
    id: str
    is_required: bool
    title: str
    value: str
    include_time: bool
