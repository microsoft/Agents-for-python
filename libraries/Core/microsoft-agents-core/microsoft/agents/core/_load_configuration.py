from typing import Any, Dict


def load_configuration_from_env(vars: Dict[str, Any]) -> dict:
    """
    Parses environment variables and returns a dictionary with the relevant configuration.
    """
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
        "AGENT_APPLICATION": result["AGENT_APPLICATION"],
        "COPILOT_STUDIO_AGENT": result["COPILOT_STUDIO_AGENT"],
        "CONNECTIONS": result["CONNECTIONS"],
        "CONNECTIONS_MAP": result["CONNECTIONS_MAP"],
    }
