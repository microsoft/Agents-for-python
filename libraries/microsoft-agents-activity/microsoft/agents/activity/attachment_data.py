from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AttachmentData(AgentsModel):
    """Attachment data.

    :param type: Content-Type of the attachment
    :type type: str
    :param name: Name of the attachment
    :type name: str
    :param original_base64: Attachment content
    :type original_base64: bytes
    :param thumbnail_base64: Attachment thumbnail
    :type thumbnail_base64: bytes
    """

    type: NonEmptyString = None
    name: NonEmptyString = None
    original_base64: bytes = None
    thumbnail_base64: bytes = None
