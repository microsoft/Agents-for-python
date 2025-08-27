# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Optional

from ..attachment import Attachment


class MessagingExtensionAttachment(AgentsModel):
    """Messaging extension attachment.

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
    :param preview: Preview attachment
    :type preview: "Attachment"
    """

    content_type: str
    content_url: str
    content: object = None
    name: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview: Attachment = None
