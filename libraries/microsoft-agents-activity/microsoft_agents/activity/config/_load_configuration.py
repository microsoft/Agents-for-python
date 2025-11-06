# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any


def load_configuration_from_env(env_vars: dict[str, Any]) -> dict:
    """
    Parses environment variables and returns a dictionary with the relevant configuration.
    """
    vars = env_vars.copy()
    result = {}
    for key, value in vars.items():
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

    return {
        "AGENTAPPLICATION": result.get("AGENTAPPLICATION", {}),
        "CONNECTIONS": result.get("CONNECTIONS", {}),
        "CONNECTIONSMAP": result.get("CONNECTIONSMAP", {}),
    }
