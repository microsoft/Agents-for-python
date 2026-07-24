# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import TypeVar
from collections.abc import Callable, Awaitable

ErrorFilter = Callable[[Exception], bool]

T = TypeVar("T")


async def ignore_error(
    promise: Awaitable[T], ignore_error_filter: ErrorFilter
) -> T | None:
    """
    Ignores errors based on the provided filter function.

    promise: the awaitable to execute
    ignore_error_filter: a function that takes an Exception and returns True if the error should be
    ignored, False otherwise.

    Returns the result of the promise if successful, or None if the error is ignored.
    Raises the error if it is not ignored.
    """
    try:
        return await promise
    except Exception as err:
        if ignore_error_filter(err):
            return None
        raise err


def is_status_code_error(*ignored_codes: int) -> ErrorFilter:
    """
    Creates an error filter function that ignores errors with specific status codes.

    ignored_codes: a list of status codes to ignore
    Returns a function that takes an Exception and returns True if the error's status code is in ignored_codes.
    """

    def func(err: Exception) -> bool:
        status_code = getattr(err, "status_code", None)
        if status_code is not None and status_code in ignored_codes:
            return True
        return False

    return func
