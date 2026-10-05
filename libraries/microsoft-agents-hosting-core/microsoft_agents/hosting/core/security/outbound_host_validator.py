# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import ipaddress
import logging

from functools import lru_cache

from aiohttp import ClientSession
from aiohttp.abc import ResolveResult

from yarl import URL

from ._connector import _ResolveResultValidator, _SSRFConnector, _SSRFError
from ._validator import _OutboundHostValidator
from ._middleware import _validator_middleware
from ._utils import _normalize_host, _try_create_url

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


def _allow_addr(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
    allow_private_network_addresses: bool,
) -> bool:
    if address.is_multicast:
        return False
    if address.is_global:
        return True
    if address.is_private and allow_private_network_addresses:
        return True
    return False


class _BasicResolveResultValidator(_ResolveResultValidator):
    """Validates resolved network addresses used by the SSRF-safe connector."""

    def __init__(self, *, allow_private_network_addresses: bool = False):
        self._allow_private_network_addresses = allow_private_network_addresses

    def is_allowed(self, resolved: ResolveResult) -> bool:

        host = resolved.get("host")

        if not host:
            return False

        try:
            address = ipaddress.ip_address(host)
            if not _allow_addr(address, self._allow_private_network_addresses):
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
        self._enabled = bool(hosts) if enabled is None else enabled

        self._hosts: set[str] = set()

        for host in hosts or []:
            normalized_host = _normalize_host(host)
            if normalized_host:
                self._hosts.add(normalized_host)
            else:
                logger.warning("Failed to normalize host: %s", host)

        self._allow_private_network_addresses = allow_private_network_addresses

        if include_default_microsoft_hosts:
            for host in _DEFAULT_MICROSOFT_HOSTS:
                normalized_host = _normalize_host(host)
                if normalized_host:
                    self._hosts.add(normalized_host)
                else:
                    logger.warning("Failed to normalize host: %s", host)

        self._resolved_validator = _BasicResolveResultValidator(
            allow_private_network_addresses=self._allow_private_network_addresses
        )

    @property
    def enabled(self) -> bool:
        """Indicates whether the outbound host validator is enabled."""
        return self._enabled

    def client(self, client_session_kwargs: dict | None = None) -> ClientSession:
        """Creates a new client session with the outbound host validator applied.
        :param client_session_kwargs: Optional keyword arguments to pass to the ClientSession constructor.
        :return: A new client session with the outbound host validator applied.
        """

        if "connector" in (client_session_kwargs or {}):
            raise ValueError("Specifying a custom connector is not allowed.")
        if "connector_owner" in (client_session_kwargs or {}):
            raise ValueError("Specifying a connector_owner value is not allowed.")
        if "middlewares" in (client_session_kwargs or {}):
            raise ValueError("Specifying custom middlewares is not allowed.")

        middleware = [_validator_middleware(self)]

        if not self._enabled:
            return ClientSession(**(client_session_kwargs or {}))

        return ClientSession(
            connector=_SSRFConnector(self._resolved_validator),
            connector_owner=True,
            middlewares=middleware,
            **(client_session_kwargs or {}),
        )

    def is_allowed(self, url: str | URL) -> bool:
        """
        Checks if the given URL is allowed based on the configured hosts and network address rules.

        :param url: The URL string or URL object to check.
        :return: True if the URL is allowed, False otherwise.
        """
        try:
            if not self._enabled:
                return True
            return self._is_allowed(url)
        except _SSRFError:
            return False

    @lru_cache
    def _is_allowed(self, _url: str | URL) -> bool:
        """
        Determines if the given URL is allowed based on the configured hosts and network address rules.

        :param _url: The URL string or URL object to check.
        :return: True if the URL is allowed, False otherwise.
        """
        url = _try_create_url(_url)
        if not url:
            logger.warning("Invalid URL: %s", _url)
            return False

        if url.host is None:
            return False

        if url.scheme != "https":
            return False

        # disallow user info in the URL (scheme://user:password@localhost)
        if url.user or url.password:
            return False

        if not url.host:
            return False

        try:
            address = ipaddress.ip_address(url.host)
            if not _allow_addr(address, self._allow_private_network_addresses):
                return False

        except ValueError:
            pass

        url_host = url.host.casefold()

        for valid_host in self._hosts:
            if url_host == valid_host or url_host.endswith("." + valid_host):
                return True
        return False
