# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pydantic import BaseModel
from typing import Optional


class AppBasedLinkQuery(BaseModel):
    """Invoke request body type for app-based link query.

    :param url: Url queried by user
    :type url: Optional[str]
    :param state: The magic code for OAuth Flow
    :type state: Optional[str]
    """

    url: Optional[str]
    state: Optional[str]
