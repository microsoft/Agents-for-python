# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""CLI configuration loading and management.

Handles loading environment variables from .env files and providing
access to authentication credentials and service URLs.
"""

import os
from pathlib import Path

from dotenv import dotenv_values


def load_environment(
    env_path: str | None = None,
) -> tuple[dict, str]:
    """Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to ".env" in current directory.
        override: Whether to override existing environment variables.
        
    Returns:
        The resolved path to the loaded .env file.
        
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
    """
    path = Path(env_path) if env_path else Path(".env")
    
    if not path.exists():
        return {}, None
    
    resolved_path = str(path.resolve())
    
    env = dotenv_values(str(resolved_path))

    return env, resolved_path

def _upper(d: dict) -> dict:
    """Convert all keys in the dictionary to uppercase."""
    return { key.upper(): value for key, value in d.items() }


class CLIConfig:
    """Configuration manager for the CLI.
    
    Loads and manages configuration from environment files and process
    environment variables, providing access to authentication credentials
    and service URLs.
    
    Attributes:
        env_path: Path to the loaded .env file, if any.
        env: Dictionary of loaded environment variables.
        app_id: Azure AD application (client) ID.
        app_secret: Azure AD application secret.
        tenant_id: Azure AD tenant ID.
        agent_url: URL of the agent service endpoint.
        service_url: Callback service URL for receiving responses.
    """

    def __init__(self, env_path: str | None, connection: str) -> None:

        env, resolved_path = load_environment(env_path)

        self._env_path: str | None = resolved_path
        self._env = _upper(env)

        # environment set before process
        self._process_env = _upper(dict(os.environ))
        self._connection = connection.upper()

        self._app_id: str | None = None
        self._app_secret: str | None = None
        self._tenant_id: str | None = None
        self._agent_url: str | None = None
        self._service_url: str | None = None

        self._load(self._env, {
            f"CONNECTIONS__{self._connection}__SETTINGS__CLIENTID": "_app_id",
            f"CONNECTIONS__{self._connection}__SETTINGS__CLIENTSECRET": "_app_secret",
            f"CONNECTIONS__{self._connection}__SETTINGS__TENANTID": "_tenant_id",
            "AGENT_URL": "_agent_url",
            "SERVICE_URL": "_service_url",
        })

    @property
    def env_path(self) -> str | None:
        """The path to the loaded environment file, if any."""
        return self._env_path

    @property
    def env(self) -> dict:
        """The loaded environment variables."""
        return self._env
    
    @property
    def app_id(self) -> str | None:
        """The application (client) ID."""
        return self._app_id
    
    @property
    def app_secret(self) -> str | None:
        """The application (client) secret."""
        return self._app_secret
    
    @property
    def tenant_id(self) -> str | None:
        """The tenant ID."""
        return self._tenant_id
    
    @property
    def agent_url(self) -> str | None:
        """The agent service URL."""
        return self._agent_url
    
    @property
    def service_url(self) -> str | None:
        """The service URL."""
        return self._service_url
    
    def _load(self, source_dict: dict, key_attr_map: dict) -> None:
        """Load configuration values from a source dictionary."""
        for key, attr_name in key_attr_map.items():
            if key in source_dict:
                value = source_dict[key]
                setattr(self, attr_name, value)