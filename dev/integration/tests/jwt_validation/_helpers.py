# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import asyncio

from microsoft_agents.hosting.core.authorization import AgentAuthConfiguration
from microsoft_agents.testing.core.utils import (
    generate_token_from_auth_config,
    load_sdk_config_connection,
)

def clone_auth_config_for_audience(
    config: AgentAuthConfiguration, audience: str
) -> AgentAuthConfiguration:
    return AgentAuthConfiguration(
        auth_type=config.AUTH_TYPE,
        client_id=audience,
        tenant_id=config.TENANT_ID,
        client_secret=config.CLIENT_SECRET,
        cert_pfx_file=config.CERT_PFX_FILE,
        authority=config.AUTHORITY,
        scopes=config.SCOPES,
        anonymous_allowed=False,
    )


async def acquire_real_service_connection_token() -> tuple[str, AgentAuthConfiguration]:
    auth_config = load_sdk_config_connection()
    token = await asyncio.to_thread(generate_token_from_auth_config, auth_config)
    return token, auth_config


def auth_config_with_invalid_audience(
    config: AgentAuthConfiguration,
) -> AgentAuthConfiguration:
    return clone_auth_config_for_audience(config, f"{config.CLIENT_ID}-invalid")
