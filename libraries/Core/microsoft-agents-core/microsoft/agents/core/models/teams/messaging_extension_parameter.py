# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel


class MessagingExtensionParameter(BaseModel):
    """Messaging extension query parameters.

    :param name: Name of the parameter
    :type name: str
    :param value: Value of the parameter
    :type value: Any
    """

    name: str = None
    value: object = None
