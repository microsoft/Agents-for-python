from typing import Any

def _list_out_seq_dicts(node) -> Any:
    """ Converts any dictionaries with integer keys to a list if the keys are sequential integers starting from 0."""

    if isinstance(node, dict):
        keys = node.keys()
        num_keys = len(keys)
        if set(keys) == set(range(num_keys)):
            # this is a seq dict
            return [
                _list_out_seq_dicts(node[i]) for i in range(num_keys)
            ]
    return node

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

    result = _list_out_seq_dicts(result)

    return {
        "AGENTAPPLICATION": result.get("AGENTAPPLICATION", {}),
        "CONNECTIONS": result.get("CONNECTIONS", {}),
        "CONNECTIONSMAP": result.get("CONNECTIONSMAP", {}),
    }
