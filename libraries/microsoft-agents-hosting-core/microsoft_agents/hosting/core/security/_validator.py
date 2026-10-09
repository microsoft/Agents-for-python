# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging

from typing import Protocol
from yarl import URL

from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class _URLValidator(Protocol):
    """Protocol for URL validators."""

    def is_allowed(self, url: str | URL) -> bool:
        """Checks if the given URL is allowed.

        :param url: The URL to check.
        :return: True if the URL is allowed, False otherwise.
        """
        ...


class _OutboundHostValidator(_URLValidator, Protocol):
    """Protocol for outbound host validators."""

    def client(self, client_session_kwargs: dict | None = None) -> ClientSession:
        """Returns a client session for making outbound requests.

        :param client_session_kwargs: Optional keyword arguments to pass to the ClientSession constructor.
        :return: A ClientSession instance.
        """
        ...
