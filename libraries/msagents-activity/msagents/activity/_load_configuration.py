from typing import Any, Dict


def load_configuration_from_env(env_vars: Dict[str, Any]) -> dict:
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

    return {
        "AGENTAPPLICATION": result.get("AGENTAPPLICATION", {}),
        "CONNECTIONS": result.get("CONNECTIONS", {}),
        "CONNECTIONSMAP": result.get("CONNECTIONSMAP", {}),
    }
