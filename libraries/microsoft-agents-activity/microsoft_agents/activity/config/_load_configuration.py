# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from .configuration import Configuration

from ._logging import _configure_logging
from . import _utils

def load_configuration_from_env(env_vars: Mapping[str, Any], defaults: Mapping[str, Any] | None = None) -> Configuration:
    """
    Parses environment variables and returns a Configuration object with the relevant configuration.

    :param env_vars: A mapping of environment variable names to their values.
    :param defaults: A mapping of default configuration values.
    :return: A Configuration object containing the resolved configuration.
    """
    local_vars = dict(env_vars)

    resolved = _utils._resolve(local_vars, defaults or {})

    if resolved.get("CONNECTIONSMAP") and isinstance(resolved["CONNECTIONSMAP"], dict):
        resolved["CONNECTIONSMAP"] = [
            conn for conn in resolved.get("CONNECTIONSMAP", {}).values()
        ]

    _configure_logging(resolved.get("LOGGING", {}))

    return Configuration({
        "AgentApplication": resolved.pop("AGENTAPPLICATION", {}),
        "Connections": resolved.pop("CONNECTIONS", {}),
        "ConnectionsMap": resolved.pop("CONNECTIONSMAP", []),
        **resolved
    })