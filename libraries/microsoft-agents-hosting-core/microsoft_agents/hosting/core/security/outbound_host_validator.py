# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ipaddress
import logging

from functools import lru_cache

from aiohttp import ClientSession
from aiohttp.abc import ResolveResult

from yarl import URL

from ._connector import _ResolveResultValidator, _SSRFConnector
from ._validator import _OutboundHostValidator
from ._middleware import _validator_middleware
from ._utils import _normalize_host

logger = logging.getLogger(__name__) 

_DEFAULT_MICROSOFT_HOSTS = [
    "botframework.com",  # Bot Connector / channel services URLs
    "smba.trafficmanager.net",  # Teams service URLs
    "teams.microsoft.com",
    "teams.microsoft.us",
    "graph.microsoft.com",  # Microsoft Graph
    "sharepoint.com",  # Sharepoint / OneDrive hosted attachments
    "svc.ms",  # Teams attachment CDN
    "blob.core.windows.net",  # Azure Blob Storage / Attachment Management Service
]

class _BasicResolveResultValidator(_ResolveResultValidator):
    """Basic implementation of the ResolveResultValidator that allows all resolved results."""

    def __init__(self, *, allow_private_network_addresses: bool = False):
        self._allow_private_network_addresses = allow_private_network_addresses

    def is_allowed(self, resolved: ResolveResult) -> bool:

        hostname = resolved.get("hostname")

        if not hostname:
            return False

        try:
            address = ipaddress.ip_address(hostname)  # Validate the resolved host IP address
            if (address.is_private or address.is_loopback) and not self._allow_private_network_addresses:
                logger.warning("Private or loopback network address not allowed")
                return False

        except ValueError:
            logger.warning("Invalid IP address")
            return False

        return True

class OutboundHostValidator(_OutboundHostValidator):
    """Outbound host validator that checks if URLs are allowed based on configured hosts and network address rules."""

    def __init__(
        self,
        hosts: list[str] | None = None,
        *,
        enabled: bool | None = None,
        include_default_microsoft_hosts: bool = True,
        allow_private_network_addresses: bool = False,
    ):
        """
        Initializes the outbound host validator.

        :param hosts: A list of allowed hosts. If None, only the default Microsoft hosts will be considered (if included).
        :param enabled: Whether the validator is enabled. If None, it will be automatically enabled if hosts are provided.
        :param include_default_microsoft_hosts: Whether to include the default Microsoft hosts in the allowed list.
        :param allow_private_network_addresses: Whether to allow private network addresses.
        """
        if hosts or enabled:
            self._enabled = True

        self._hosts: set[str] = set(hosts or [])
        self._allow_private_network_addresses = allow_private_network_addresses

        if include_default_microsoft_hosts:
            for host in _DEFAULT_MICROSOFT_HOSTS:
                normalized_host = _normalize_host(host)
                if normalized_host:
                    self._hosts.add(normalized_host)
                else:
                    logger.warning("Failed to normalize host: %s", host)

    @property
    def enabled(self) -> bool:
        """Indicates whether the outbound host validator is enabled."""
        return self._enabled

    def client(self, session: ClientSession | None = None) -> ClientSession:
        """Creates a new client session with the outbound host validator applied.
        :param session: An optional existing client session to use.
        :return: A new client session with the outbound host validator applied.
        """

        headers = session.headers if session else {}
        middleware = [_validator_middleware(self)]

        return ClientSession(
            headers=headers,
            connector=_SSRFConnector(_BasicResolveResultValidator()),
            middlewares=middleware,
        )

    def is_allowed(self, url: str | URL) -> bool:
        """
        Checks if the given URL is allowed based on the configured hosts and network address rules.

        :param url: The URL string or URL object to check.
        :return: True if the URL is allowed, False otherwise.
        """
        if not self._enabled:
            return True
        return self._is_allowed(url)

    @lru_cache
    def _is_allowed(self, url: str | URL) -> bool:
        """
        Determines if the given URL is allowed based on the configured hosts and network address rules.

        :param url: The URL string or URL object to check.
        :return: True if the URL is allowed, False otherwise.
        """
        # Is this a valid URL?
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

        if url.host is None:
            return False

        # Only allow HTTP and HTTPS schemes
        if url.scheme not in ("http", "https"):
            return False

        if url.user or url.password:
            return False

        address = None
        if url.host:
            try:
                address = ipaddress.ip_address(url.host)
                if address.is_private and not self._allow_private_network_addresses:
                    return False
                if address.is_loopback:
                    return False
                
            except ValueError:
                address = None

        for host in self._hosts:
            url_host = (host or "").casefold()
            if url.host == host or url_host.endswith("." + host):
                return True
        return False