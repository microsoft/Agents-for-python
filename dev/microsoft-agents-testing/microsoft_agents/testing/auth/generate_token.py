import requests

from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.testing.sdk_config import SDKConfig


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


def generate_token_from_config(sdk_config: SDKConfig) -> str:
    """Generates a token using a provided config object.

    :param config: Configuration dictionary containing connection settings.
    :return: Generated access token as a string.
    """

    settings: AgentAuthConfiguration = sdk_config.get_connection()

    app_id = settings.CLIENT_ID
    app_secret = settings.CLIENT_SECRET
    tenant_id = settings.TENANT_ID

    if not app_id or not app_secret or not tenant_id:
        raise ValueError("Incorrect configuration provided for token generation.")
    return generate_token(app_id, app_secret, tenant_id)
