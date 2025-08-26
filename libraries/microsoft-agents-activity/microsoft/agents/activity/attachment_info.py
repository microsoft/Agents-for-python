from .attachment_view import AttachmentView
from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class AttachmentInfo(AgentsModel):
    """Metadata for an attachment.

    :param name: Name of the attachment
    :type name: str
    :param type: ContentType of the attachment
    :type type: str
    :param views: attachment views
    :type views: list[~microsoft.agents.protocols.models.AttachmentView]
    """

    name: NonEmptyString = None
    type: NonEmptyString = None
    views: list[AttachmentView] = None
