# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel
from typing import Any, Optional


class MessageActionsPayloadAttachment(AgentsModel):
    """Represents the attachment in a message.

    :param id: The id of the attachment.
    :type id: Optional[str]
    :param content_type: The type of the attachment.
    :type content_type: Optional[str]
    :param content_url: The url of the attachment, in case of an external link.
    :type content_url: Optional[str]
    :param content: The content of the attachment, in case of a code snippet, email, or file.
    :type content: Optional[Any]
    :param name: The plaintext display name of the attachment.
    :type name: Optional[str]
    :param thumbnail_url: The url of a thumbnail image that might be embedded in the attachment, in case of a card.
    :type thumbnail_url: Optional[str]
    """

    id: Optional[str]
    content_type: Optional[str]
    content_url: Optional[str]
    content: Optional[Any]
    name: Optional[str]
    thumbnail_url: Optional[str]
