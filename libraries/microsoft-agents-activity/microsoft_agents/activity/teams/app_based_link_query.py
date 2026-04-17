# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class AppBasedLinkQuery(AgentsModel):
    """Invoke request body type for app-based link query.

    :param url: Url queried by user
    :type url: str | None
    :param state: The magic code for OAuth Flow
    :type state: str | None
    """

    url: str | None
    state: str | None
