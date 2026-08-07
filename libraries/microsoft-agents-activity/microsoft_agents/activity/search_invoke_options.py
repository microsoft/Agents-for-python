# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel


class SearchInvokeOptions(AgentsModel):
    """Defines the query options in the 'SearchInvokeValue' for Invoke activity with name of 'application/search'.

    :param skip: The number of items to skip in the search results. This is an integer that specifies how many items to skip in the search results.
    :type skip: int
    :param top: The maximum number of items to return in the search results. This is an integer that specifies the maximum number of items to return in the search results.
    :type top: int
    """

    skip: int
    top: int
