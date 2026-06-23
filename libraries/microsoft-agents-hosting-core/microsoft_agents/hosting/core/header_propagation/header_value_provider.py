# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from abc import ABC, abstractmethod


class HeaderValueProvider(ABC):
    """Provides dynamically resolved headers to inject on outgoing HTTP requests.

    Implementations are registered per-turn via
    :class:`microsoft_agents.hosting.core.header_propagation.HeaderPropagationContext`
    and are queried each time an outgoing connector client is built.
    """

    @abstractmethod
    def get_headers(self) -> dict[str, str]:
        """Returns the headers to inject on outgoing requests.

        Called each time an outgoing connector client collects propagated
        headers.

        :return: A mapping of header name to header value.
        :rtype: dict[str, str]
        """
        raise NotImplementedError
