# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .agents_model import AgentsModel
from .search_invoke_options import SearchInvokeOptions


class SearchInvokeValue(AgentsModel):
    """Defines the structure that arrives in Activity.value for invoke activity with name of 'application/search'.

    :param kind: The kind of search being performed. This is a string that is used to identify the type of search being performed.
    :type kind: str
    :param query_text: The text of the search query. This is a string that contains the text of the search query being performed.
    :type query_text: str
    :param query_options: The options for the search query. This is an object that contains the options for the search query being performed.
    :type query_options: :class:`microsoft_agents.activity.search_invoke_options.SearchInvokeOptions`
    """

    kind: str
    query_text: str
    query_options: SearchInvokeOptions
