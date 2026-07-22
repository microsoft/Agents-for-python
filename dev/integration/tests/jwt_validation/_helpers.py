# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from pathlib import Path

from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration


def load_auth_config(env_file_name: str) -> AgentAuthConfiguration:
    env_vars = dotenv_values(Path(__file__).with_name(env_file_name))
    sdk_config = load_configuration_from_env(env_vars)
    settings = sdk_config["CONNECTIONS"]["SERVICE_CONNECTION"]["SETTINGS"]
    return AgentAuthConfiguration(**settings)
