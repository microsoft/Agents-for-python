# # Copyright (c) Microsoft Corporation. All rights reserved.
# # Licensed under the MIT License.

# from typing import Callable, Awaitable, Protocol

# from aiohttp import (
#     ClientSession,
#     ClientRequest,
#     ClientHandlerType,
#     ClientResponse,
# )
# from yarl import URL
# from urllib.parse import urlparse

# _DEFAULT_MICROSOFT_HOSTS = [
#     "botframework.com",  # Bot Connector / channel services URLs
#     "smba.trafficmanager.net",  # Teams service URLs
#     "teams.microsoft.com",
#     "teams.microsoft.us",
#     "graph.microsoft.com",  # Microsoft Graph
#     "sharepoint.com",  # Sharepoint / OneDrive hosted attachments
#     "svc.ms",  # Teams attachment CDN
#     "blob.core.windows.net",  # Azure Blob Storage / Attachment Management Service
# ]


# def _try_create_url(url: str | URL) -> URL | None:
#     """Attempts to create a URL object from the given string or URL.

#     :param url: The URL string or URL object to create.
#     :return: A URL object if successful, None otherwise.
#     """
#     try:
#         return URL(url) if isinstance(url, str) else url
#     except (ValueError, TypeError):
#         return None


# def _normalize(host: str) -> str | None:
#     """Normalizes a host string to a suffix for comparison.

#     :param host: The host string to normalize.
#     :return: The normalized host suffix, or None if the input is invalid.
#     """
#     if not host:
#         return None

#     host = host.strip().casefold()

#     if host.startswith("*."):
#         host = host[2:]

#     url_obj = _try_create_url(host)
#     if url_obj and url_obj.host:
#         host = url_obj.host
#     else:
#         slash = host.find("/")
#         if slash >= 0:
#             host = host[:slash]

#         colon = host.find(":")
#         if colon >= 0:
#             host = host[:colon]

#     return host if host else None

# class OutboundHostValidatorProtocol(Protocol):

#     @property
#     def enabled(self) -> bool:
#         ...

#     def is_allowed(self, url: str | URL) -> bool:
#         ...

# class BasicOutboundHostValidator(OutboundHostValidatorProtocol):
#     def __init__(self, enabled: bool = False):
#         self._enabled = enabled

#     @property
#     def enabled(self) -> bool:
#         return self._enabled

#     def is_allowed(self, url: str | URL) -> bool:
#         """Checks whether the given URL is allowed by the basic validator.

#         :param url: The URL to check.
#         :return: True if the URL is allowed, False otherwise.
#         """
#         parsed = urlparse(str(url))
#         return parsed.scheme == "https" or (
#             parsed.scheme == "http" and parsed.hostname == "localhost"
#         )


# class OutboundHostValidator:
#     """Validates that an outbound URL targets an allowed host before the SDK makes a
#     server-side, often token-bearing, request to it (e.g. Activity.service_url callbacks or attachment
#     downloads). This is the SDK's shared anti-SSRF ("allow_hosts") control."""

#     _enabled: bool
#     _suffixes: set[str]

#     def __init__(
#         self,
#         enabled: bool = False,
#         hosts: list[str] | None = None,
#         include_default_microsoft_hosts: bool = True,
#     ):
#         """Initializes the outbound host validator.

#         :param enabled: Whether the validator is enabled.
#         :param hosts: A list of additional allowed host suffixes.
#         :param include_default_microsoft_hosts: Whether to include the default Microsoft hosts.
#         """
#         self._enabled = enabled
#         suffixes: list[str] = []
#         if include_default_microsoft_hosts:
#             suffixes.extend(_DEFAULT_MICROSOFT_HOSTS)

#         if hosts:
#             for host in hosts:
#                 normalized = _normalize(host)
#                 if normalized is not None:
#                     suffixes.append(normalized)

#         self._suffixes = set(suffixes)

#     @property
#     def enabled(self) -> bool:
#         """Gets whether the validator is enabled. If disabled, all outbound hosts are allowed."""
#         return self._enabled

#     def is_allowed(self, url: str | URL) -> bool:
#         """Checks whether the given URL is allowed by the validator.

#         :param url: The URL to check.
#         :return: True if the URL is allowed, False otherwise.
#         """
#         if not self._enabled:
#             return True

#         url_obj = _try_create_url(url)
#         if not url_obj or not url_obj.absolute or url_obj.scheme != "https":
#             return False

#         host = url_obj.host
#         if not host:
#             return False

#         host = host.casefold()

#         for suffix in self._suffixes:
#             if host == suffix or host.endswith("." + suffix):
#                 return True

#         return False

# def _validator_middleware(validator: OutboundHostValidatorProtocol | None = None) -> Callable[[ClientRequest, ClientHandlerType], Awaitable[ClientResponse]]:
#     """Creates a middleware that validates outbound URLs using the given validator.
    
#     :param validator: The outbound host validator to use.
#     :return: A middleware function that validates outbound URLs.
#     """
#     validator = validator or OutboundHostValidator(enabled=True)
        
#     async def _middleware(req: ClientRequest, handler: ClientHandlerType) -> ClientResponse:

#         if validator is not None and validator.enabled and not validator.is_allowed(req.url):
#             raise ValueError(f"URL '{req.url}' is not allowed by the outbound host validator.")

#         return await handler(req)

#     return _middleware