# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Type utilities for the fluent backend.

Provides special types like Unset (sentinel for missing values) and
SafeObject (safe attribute access that doesn't raise on missing keys).
"""

from .safe_object import SafeObject, resolve, parent
from .unset import Unset

__all__ = [
    "SafeObject",
    "resolve",
    "parent",
    "Unset",
]