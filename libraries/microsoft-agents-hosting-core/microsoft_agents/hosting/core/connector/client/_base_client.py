# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import logging
from typing import Any, Callable

from aiohttp import ClientSession

from ...header_propagation import HeaderPropagationContext

logger = logging.getLogger(__name__)


class _ClientSessionWrapper:
    """ClientSession wrapper that merges propagated headers per request."""

    def __init__(self, session: ClientSession):
        self._session = session

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)

    def _separate_headers(self, **kwargs) -> tuple[dict, dict]:
        """
        Separate headers from other keyword arguments.

        :param kwargs: Keyword arguments that may contain headers.
        :return: A tuple containing the headers and the remaining keyword arguments.
        """
        headers = dict(kwargs.get("headers") or {})
        kwargs_without_headers = {k: v for k, v in kwargs.items() if k != "headers"}
        return headers, kwargs_without_headers

    def _apply_headers(self, headers: dict) -> None:
        """
        Merge propagated headers into the request headers.

        Explicit request headers take precedence over propagated values with the
        same name.

        :param headers: Mutable request headers to augment.
        """
        propagated_headers = HeaderPropagationContext.collect_headers()
        if propagated_headers:
            for key, value in propagated_headers.items():
                headers.setdefault(key, value)
            logger.debug(
                "Applying propagated headers: %s", list(propagated_headers.keys())
            )

    def _call_with_headers(self, method: Callable, *args, **kwargs):
        """
        Call the underlying session method with propagated headers merged.

        :param method: The HTTP method to call.
        :param args: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.
        :return: The result of the method call.
        """
        headers, kwargs_without_headers = self._separate_headers(**kwargs)
        self._apply_headers(headers)
        return method(*args, headers=headers, **kwargs_without_headers)

    def request(self, *args, **kwargs):
        return self._call_with_headers(self._session.request, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._call_with_headers(self._session.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._call_with_headers(self._session.post, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._call_with_headers(self._session.put, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._call_with_headers(self._session.delete, *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._call_with_headers(self._session.patch, *args, **kwargs)


class _BaseClient:

    def __init__(self, client: ClientSession):
        self._client = client

    def _wrapped_client(self) -> _ClientSessionWrapper:
        """
        Returns a session wrapper that merges propagated headers per request.

        :return: The wrapped ClientSession.
        """
        return _ClientSessionWrapper(self._client)
