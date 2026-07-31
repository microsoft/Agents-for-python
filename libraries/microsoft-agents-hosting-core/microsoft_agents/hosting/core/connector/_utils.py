# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from logging import Logger

import aiohttp


def _handle_request_error(
    logger: Logger, response: aiohttp.ClientResponse, resource: str = "resource"
) -> None:

    if response.status == 400:
        logger.error("Bad request for '%s': %s", resource, response.status)
    else:
        logger.error("Error accessing '%s': %s", resource, response.status)

    if not response.ok:
        response.raise_for_status()

    raise aiohttp.ClientResponseError(
        response.request_info,
        response.history,
        status=response.status,
        message=f"Error accessing resource '{resource}'",
        headers=response.headers,
    )
