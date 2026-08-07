# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .search_invoke_value import SearchInvokeValue


class AdaptiveCardSearchInvokeValue(SearchInvokeValue):
    """
    :param dataset: The dataset for this adaptive card search value.
    :type dataset: str
    """

    dataset: str | None = None
