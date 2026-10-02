# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Callable, Awaitable

from aiohttp import ClientRequest, ClientHandlerType, ClientResponse

from ._validator import _URLValidator, _SSRFError


def _validator_middleware(
    validator: _URLValidator,
) -> Callable[[ClientRequest, ClientHandlerType], Awaitable[ClientResponse]]:
    """Creates a middleware that validates outbound URLs using the given validator.

    :param validator: The outbound host validator to use.
    :return: A middleware function that validates outbound URLs.
    """

    async def _middleware(
        req: ClientRequest, handler: ClientHandlerType
    ) -> ClientResponse:
        """Middleware that validates outbound URLs using the given host validator."""

        if not validator.is_allowed(req.url):
            raise _SSRFError(
                f"URL '{req.url}' is not allowed by the outbound host validator."
            )

        return await handler(req)

    return _middleware
