# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Mapping,
    Protocol,
    runtime_checkable,
)
from typing_extensions import Self


@runtime_checkable
class _MappingConfigurable(Protocol):
    """Structural contract for constructing an object from a mapping."""

    @classmethod
    def from_config(cls, _mapping: Mapping) -> Self: ...
