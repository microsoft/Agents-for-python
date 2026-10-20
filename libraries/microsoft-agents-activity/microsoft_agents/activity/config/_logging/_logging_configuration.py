# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass

from microsoft_agents.activity.errors import configuration_errors
from .._configuration_protocol import _DictConfigurable
from ._constants import _NAME_TO_LEVEL

_K_LOG_LEVEL = "LOGLEVEL"

@dataclass(frozen=True)
class _LogLevelEntry:
    """Represents a logging level entry with a namespace and level."""

    namespace: str
    level: int

    def __init__(self, namespace: str, level: str) -> None:
        level_upper = level.upper()
        if level_upper not in _NAME_TO_LEVEL:
            raise ValueError(
                configuration_errors.InvalidLoggingConfiguration.format(namespace, level)
            )
        object.__setattr__(self, "namespace", namespace.lower())
        object.__setattr__(self, "level", _NAME_TO_LEVEL[level_upper])

@dataclass(frozen=True)
class _LoggingConfiguration(_DictConfigurable):
    """Configuration class for logging levels."""

    log_levels: list[_LogLevelEntry]


    def __init__(self, data: dict) -> None:
        """Initialize the logging configuration from a dictionary."""

        raw_log_levels = data.get(_K_LOG_LEVEL, {})
        log_levels: list[_LogLevelEntry] = [
            _LogLevelEntry(namespace, level)
            for namespace, level in raw_log_levels.items()
        ]

        object.__setattr__(self, "log_levels", log_levels)