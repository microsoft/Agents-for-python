from os import environ
from microsoft_agents.authentication.msal import AuthTypes, MsalAuthConfiguration
from microsoft_agents.hosting.core.client import (
    ChannelHostConfiguration,
    ChannelsConfiguration,
    ChannelInfo,
)


class DefaultConfig(MsalAuthConfiguration, ChannelsConfiguration):
    """Agent Configuration"""

    def __init__(self) -> None:
        self.AUTH_TYPE = AuthTypes.client_secret
        self.TENANT_ID = "" or environ.get("TENANT_ID")
        self.CLIENT_ID = "" or environ.get("CLIENT_ID")
        self.CLIENT_SECRET = "" or environ.get("CLIENT_SECRET")
        self.PORT = 3978
        self.SCOPES = ["https://api.botframework.com/.default"]

    # ChannelHost configuration
    @staticmethod
    def CHANNEL_HOST_CONFIGURATION():
        return ChannelHostConfiguration(
            CHANNELS=[
                ChannelInfo(
                    id="EchoAgent",
                    app_id="" or environ.get("TARGET_APP_ID"),  # Target agent's app_id
                    resource_url="http://localhost:3999/api/messages",
                    token_provider="ChannelConnection",
                    channel_factory="HttpAgentClient",
                    endpoint="http://localhost:3999/api/messages",
                )
            ],
            HOST_ENDPOINT="http://localhost:3978/api/botresponse/",
            HOST_APP_ID="" or environ.get("CLIENT_ID"),  # usually the same as CLIENT_ID
        )
