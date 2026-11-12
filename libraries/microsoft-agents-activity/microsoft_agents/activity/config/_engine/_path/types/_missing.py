# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any
from typing_extensions import TypeIs


class _MissingType:
    """A special class used to represent missing values in the configuration."""

    def __bool__(self):
        return False


_MISSING = _MissingType()  # Singleton instance representing a missing value


def _is_missing(val: Any) -> TypeIs[_MissingType]:
    """Check if a value is the special _MissingType instance.

    :param val: The value to check.
    :return: True if the value is an instance of _MissingType, False otherwise.
    """
    return isinstance(val, _MissingType)
