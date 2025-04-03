from pydantic import BaseModel
from typing import Optional


class MessagingExtensionAttachment(BaseModel):
    """Messaging extension attachment.

    :param content_type: mimetype/Contenttype for the file
    :type content_type: str
    :param content_url: Content Url
    :type content_url: str
    :param content: Embedded content
    :type content: Optional[object]
    :param name: (OPTIONAL) The name of the attachment
    :type name: Optional[str]
    :param thumbnail_url: (OPTIONAL) Thumbnail associated with attachment
    :type thumbnail_url: Optional[str]
    :param preview: Preview attachment
    :type preview: Optional["Attachment"]
    """

    content_type: str
    content_url: str
    content: Optional[object]
    name: Optional[str]
    thumbnail_url: Optional[str]
    preview: Optional["Attachment"]
