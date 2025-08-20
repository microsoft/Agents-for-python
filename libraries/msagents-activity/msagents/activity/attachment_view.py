from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AttachmentView(AgentsModel):
    """Attachment View name and size.

    :param view_id: Id of the attachment
    :type view_id: str
    :param size: Size of the attachment
    :type size: int
    """

    view_id: NonEmptyString = None
    size: int = None
