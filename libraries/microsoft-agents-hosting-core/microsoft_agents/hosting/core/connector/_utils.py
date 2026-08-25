# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from logging import Logger

import aiohttp


def _handle_request_error(
    logger: Logger,
    response: aiohttp.ClientResponse,
    resource: str = "resource",
    response_body: str | None = None,
) -> None:

    if response.status == 400:
        logger.error("Bad request for '%s': %s", resource, response.status)
    else:
        logger.error("Error accessing '%s': %s", resource, response.status)

    if not response.ok and response_body:
        raise aiohttp.ClientResponseError(
            response.request_info,
            response.history,
            status=response.status,
            message=response_body,
            headers=response.headers,
        )

    if not response.ok:
        response.raise_for_status()

    raise aiohttp.ClientResponseError(
        response.request_info,
        response.history,
        status=response.status,
        message=f"Error accessing resource '{resource}'",
        headers=response.headers,
    )
