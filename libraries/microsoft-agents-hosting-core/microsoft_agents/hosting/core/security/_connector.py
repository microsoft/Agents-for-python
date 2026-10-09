# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Sequence
from typing import Protocol

from aiohttp import TCPConnector
from aiohttp.abc import ResolveResult
from aiohttp.tracing import Trace


class _ResolveResultValidator(Protocol):
    """Protocol for validating resolved results to prevent SSRF attacks."""

    def is_allowed(self, resolved: ResolveResult) -> bool:
        """Check if the resolved result is valid to prevent SSRF attacks.

        :param resolved: The resolved result to validate.
        :return: True if the resolved result is valid, False otherwise.
        """
        ...


class _SSRFError(ValueError):
    """Exception raised when an SSRF attack is detected."""


class _SSRFConnector(TCPConnector):
    """TCPConnector subclass that validates resolved host results to prevent SSRF attacks."""

    def __init__(
        self, resolved_result_validator: _ResolveResultValidator, *args, **kwargs
    ):
        """Initialize the SSRFConnector with a resolved result validator.

        :param resolved_result_validator: The validator used to check resolved host results.
        """
        super().__init__(*args, **kwargs)
        self._resolved_result_validator = resolved_result_validator

    async def _resolve_host(
        self, host: str, port: int, traces: Sequence[Trace] | None = None
    ) -> list[ResolveResult]:
        """Resolve the host and validate the resolved results to prevent SSRF attacks.

        :param host: The hostname to resolve.
        :param port: The port number to resolve.
        :param traces: Optional sequence of Trace objects for tracing the resolution process.
        :return: A list of validated ResolveResult objects.
        :raises _SSRFError: If any resolved result is invalid.
        """

        res = await super()._resolve_host(host, port, traces)

        for r in res:
            if not self._resolved_result_validator.is_allowed(r):
                raise _SSRFError(f"Invalid resolved result: {r}")
        return res
