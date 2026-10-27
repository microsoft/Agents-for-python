# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio

from dotenv import dotenv_values

from microsoft_agents.activity import load_configuration_from_env
from microsoft_agents.activity.config import Configuration
from microsoft_agents.hosting.testing.core.utils import (
    generate_token_from_config,
)


async def acquire_real_service_connection_token() -> tuple[str, Configuration]:
    auth_config = Configuration(load_configuration_from_env(dotenv_values(".env")))
    token = await asyncio.to_thread(generate_token_from_config, auth_config)
    return token, auth_config


def auth_config_with_invalid_audience(
    config: Configuration,
) -> Configuration:
    return Configuration.from_mapping(
        {
            "TOKEN_VALIDATION": {
                "AUDIENCES": ["invalid-audience"],
                "ANONYMOUS_ALLOWED": False,
            }
        },
        **config,
    )
