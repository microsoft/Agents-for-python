# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Mapping

from ._logging import _configure_logging
from ._resolve import _resolve


def load_configuration_from_env(env_vars: Mapping[str, Any]) -> dict:
    """
    Parses environment variables and returns a dictionary with the relevant configuration.
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

    # temporary fix before next PR
    token_validation_options = _resolve(
        result.get("TOKENVALIDATION", {}),
    )

    return {
        "AGENTAPPLICATION": result.pop("AGENTAPPLICATION", {}),
        "CONNECTIONS": result.pop("CONNECTIONS", {}),
        "CONNECTIONSMAP": result.pop("CONNECTIONSMAP", []),
        "LOGGING": result.pop("LOGGING", {}),
        "TOKENVALIDATION": token_validation_options,
    }
