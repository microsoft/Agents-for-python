# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from copy import deepcopy
from dotenv import load_dotenv, dotenv_values
from typing import Optional

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core import AgentAuthConfiguration


class SDKConfig:
    """Loads and provides access to SDK configuration from a .env file or environment variables.

    Immutable access to the configuration dictionary is provided via the `config` property.
    """

    def __init__(
        self, env_path: Optional[str] = None, load_into_environment: bool = False
    ):
        """Initializes the SDKConfig by loading configuration from a .env file or environment variables.

        :param env_path: Optional path to the .env file. If None, defaults to '.env' in the current directory.
        :param load_into_environment: If True, loads the .env file directly into the configuration dictionary (does NOT load into environment variables). If False, loads the .env file into environment variables first, then loads the configuration from those environment variables.
        """
        if load_into_environment:
            self._config = load_configuration_from_env(
                dotenv_values(env_path)
            )  # Load .env file
        else:
            load_dotenv(env_path)  # Load .env file into environment variables
            self._config = load_configuration_from_env(
                os.environ
            )  # Load from environment variables

    @property
    def config(self) -> dict:
        """Returns the loaded configuration dictionary."""
        return deepcopy(self._config)

    def get_connection(
        self, connection_name: str = "SERVICE_CONNECTION"
    ) -> AgentAuthConfiguration:
        """Creates an AgentAuthConfiguration from a provided config object."""
        data = self._config["CONNECTIONS"][connection_name]["SETTINGS"]
        return AgentAuthConfiguration(**data)
