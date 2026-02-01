# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Core utility functions for the testing framework.

Provides helper functions for token generation, configuration handling,
and activity manipulation.
"""

import requests

from microsoft_agents.activity import Activity
from microsoft_agents.hosting.core import AgentAuthConfiguration

from .transport import Exchange

def activities_from_ex(exchanges: list[Exchange]) -> list[Activity]:
    """Extracts all response activities from a list of exchanges."""
    activities: list[Activity] = []
    for exchange in exchanges:
        activities.extend(exchange.responses)
    return activities

def sdk_config_connection(
    sdk_config: dict, connection_name: str = "SERVICE_CONNECTION"
) -> AgentAuthConfiguration:
    """Creates an AgentAuthConfiguration from a provided config object."""
    data = sdk_config["CONNECTIONS"][connection_name]["SETTINGS"]
    return AgentAuthConfiguration(**data)

# TODO -> use MsalAuth to generate token
# TODO -> support other forms of auth (certificates, etc)
def generate_token(app_id: str, app_secret: str, tenant_id: str) -> str:
    """Generate a token using the provided app credentials.

    :param app_id: Application (client) ID.
    :param app_secret: Application client secret.
    :param tenant_id: Directory (tenant) ID.
    :return: Generated access token as a string.
    """

    authority_endpoint = (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    )

    res = requests.post(
        authority_endpoint,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "client_id": app_id,
            "client_secret": app_secret,
            "scope": f"{app_id}/.default",
        },
        timeout=10,
    )
    return res.json().get("access_token")


def generate_token_from_config(sdk_config: dict, connection_name: str = "SERVICE_CONNECTION") -> str:
    """Generates a token using a provided config object.

    :param sdk_config: Configuration dictionary containing connection settings.
    :param connection_name: Name of the connection to use from the config.
    :return: Generated access token as a string.
    """

    settings: AgentAuthConfiguration = sdk_config_connection(sdk_config, connection_name)

    client_id = settings.CLIENT_ID
    client_secret = settings.CLIENT_SECRET
    tenant_id = settings.TENANT_ID

    if not client_id or not client_secret or not tenant_id:
        raise ValueError("Incorrect configuration provided for token generation.")
    return generate_token(client_id, client_secret, tenant_id)
