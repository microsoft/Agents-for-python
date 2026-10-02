# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ipaddress
import logging

from typing import Protocol
from yarl import URL

logger = logging.getLogger(__name__)

class _URLValidator(Protocol):

    def is_allowed(self, url: str | URL) -> bool:
        ...

class OutboundHostValidator(_URLValidator):

    def __init__(self, enabled: bool = False):
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def is_allowed(self, url: str | URL) -> bool:
        if not self._enabled:
            return True

        url_str: str
        if isinstance(url, str):
            url_str = url
            try:
                url = URL(url)
            except ValueError:
                logger.warning("Invalid URL: %s", url)
                return False
        else:
            url_str = str(url)

        if url.scheme not in ("http", "https"):
            return False

        if url.user or url.password:
            return False

        if url.absolute:
            
        
        

        if url.userinfo:

        host = url.host if isinstance(url, URL) else URL(url).host