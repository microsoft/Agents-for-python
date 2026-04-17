# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any

from ..agents_model import AgentsModel


class MessageActionsPayloadAttachment(AgentsModel):
    """Represents the attachment in a message.

    :param id: The id of the attachment.
    :type id: str | None
    :param content_type: The type of the attachment.
    :type content_type: str | None
    :param content_url: The url of the attachment, in case of an external link.
    :type content_url: str | None
    :param content: The content of the attachment, in case of a code snippet, email, or file.
    :type content: Any | None
    :param name: The plaintext display name of the attachment.
    :type name: str | None
    :param thumbnail_url: The url of a thumbnail image that might be embedded in the attachment, in case of a card.
    :type thumbnail_url: str | None
    """

    id: str | None
    content_type: str | None
    content_url: str | None
    content: Any | None
    name: str | None
    thumbnail_url: str | None
