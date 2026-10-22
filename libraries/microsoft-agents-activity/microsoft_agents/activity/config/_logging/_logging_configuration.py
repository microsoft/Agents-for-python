# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass

from microsoft_agents.activity.errors import configuration_errors

from ..configuration import Configuration, _Configurable
from .._utils import _xpath
from ._constants import _NAME_TO_LEVEL


@dataclass(frozen=True)
class _LogLevelEntry:
    """Represents a logging level entry with a namespace and level."""

    namespace: str
    level: int

    def __init__(self, namespace: str, level: str) -> None:
        level_upper = level.upper()
        if level_upper not in _NAME_TO_LEVEL:
            raise ValueError(
                configuration_errors.InvalidLoggingConfiguration.format(
                    namespace, level
                )
            )
        object.__setattr__(self, "namespace", namespace.lower())
        object.__setattr__(self, "level", _NAME_TO_LEVEL[level_upper])

@dataclass(frozen=True)
class _LoggingConfiguration(_Configurable):
    """Configuration class for logging levels."""

    log_levels: list[_LogLevelEntry]

    @classmethod
    def _from_configuration(cls, config: Configuration) -> _LoggingConfiguration:

        raw_log_levels = config.get(_xpath("log_level"), default={})
        if not isinstance(raw_log_levels, dict):
            raise ValueError(
                configuration_errors.InvalidLoggingConfiguration.format(
                    "log_levels", raw_log_levels
                )
            )
        log_levels: list[_LogLevelEntry] = [
            _LogLevelEntry(namespace, level)
            for namespace, level in raw_log_levels.items()
        ]
        return cls(log_levels)