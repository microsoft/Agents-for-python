# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from ._configure_logging import _configure_logging
from .configuration import Configuration


def load_configuration_from_env(env_vars: Mapping[str, Any]) -> Configuration:
    """
    Parses environment variables and returns a Configuration object with the relevant configuration.
    """
    local_vars = dict(env_vars)
    result = {}
    for key, value in local_vars.items():
        levels = key.split("__")
        current_level = result
        last_level = None
        for next_level in levels:
            if next_level not in current_level:
                current_level[next_level] = {}
            last_level = current_level
            current_level = current_level[next_level]
        last_level[levels[-1]] = value

    if result.get("CONNECTIONSMAP") and isinstance(result["CONNECTIONSMAP"], dict):
        result["CONNECTIONSMAP"] = [
            conn for conn in result.get("CONNECTIONSMAP", {}).values()
        ]

    _configure_logging(result.get("LOGGING", {}))

    return Configuration({
        "AgentApplication": result.pop("AGENTAPPLICATION", {}),
        "Connections": result.pop("CONNECTIONS", {}),
        "ConnectionsMap": result.pop("CONNECTIONSMAP", []),
        **result
    })