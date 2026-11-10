# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from microsoft_agents.activity.errors import configuration_errors

from ..configuration import Configuration, _RootConfigurable
from .._utils import _legpath as legpath
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
class _LoggingConfiguration(_RootConfigurable):
    """Bind namespace log levels from root configuration or a logging section.

    Root input reads ``logging::log_level``; scoped input reads ``log_level``
    directly. Missing entries produce no level overrides.
    """

    log_levels: list[_LogLevelEntry]

    @classmethod
    def _from_root_configuration(cls, config: Configuration) -> _LoggingConfiguration:
        return cls._from_scoped_configuration(
            config.get_section(legpath("logging"), default=Configuration())
        )

    @classmethod
    def _from_scoped_configuration(cls, config: Configuration) -> _LoggingConfiguration:

        raw_log_levels = config.get(legpath("log_level"), default={})
        if not isinstance(raw_log_levels, Mapping):
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
