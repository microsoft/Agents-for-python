def create_env_var_dict(env_raw: str) -> dict[str, str]:
    """Create a dictionary from a string that represents a .env config file."""
    lines = env_raw.strip().split("\n")
    env = {}
    for line in lines:
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env