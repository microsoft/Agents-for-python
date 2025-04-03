from pydantic import BaseModel


class OnBehalfOf(BaseModel):
    """Specifies the OnBehalfOf entity for meeting notifications.

    :param item_id: The item id of the OnBehalfOf entity.
    :type item_id: str
    :param display_name: The display name of the OnBehalfOf entity.
    :type display_name: str
    :param mri: The MRI of the OnBehalfOf entity.
    :type mri: str
    """

    item_id: str
    display_name: str
    mri: str
