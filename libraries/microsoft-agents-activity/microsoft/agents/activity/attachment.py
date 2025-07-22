from .agents_model import AgentsModel
from ._type_aliases import NonEmptyString


class Attachment(AgentsModel):
    """An attachment within an activity.

    :param content_type: mimetype/Contenttype for the file
    :type content_type: str
    :param content_url: Content Url
    :type content_url: str
    :param content: Embedded content
    :type content: object
    :param name: (OPTIONAL) The name of the attachment
    :type name: str
    :param thumbnail_url: (OPTIONAL) Thumbnail associated with attachment
    :type thumbnail_url: str
    """

    content_type: NonEmptyString
    content_url: NonEmptyString = None
    content: object = None
    name: NonEmptyString = None
    thumbnail_url: NonEmptyString = None
