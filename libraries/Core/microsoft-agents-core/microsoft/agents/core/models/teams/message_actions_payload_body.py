# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class MessageActionsPayloadBody(BaseModel):
    """Plaintext/HTML representation of the content of the message.

    :param content_type: Type of the content. Possible values include: 'html', 'text'
    :type content_type: str
    :param content: The content of the body.
    :type content: str
    """

    content_type: str = None
    content: str = None
