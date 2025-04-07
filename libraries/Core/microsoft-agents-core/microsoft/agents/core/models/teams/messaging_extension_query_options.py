# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ..agents_model import AgentsModel


class MessagingExtensionQueryOptions(AgentsModel):
    """Messaging extension query options.

    :param skip: Number of entities to skip
    :type skip: int
    :param count: Number of entities to fetch
    :type count: int
    """

    skip: int = None
    count: int = None
