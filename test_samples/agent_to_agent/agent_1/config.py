from microsoft.agents.authorization.msal import AuthTypes, MsalAuthConfiguration
from microsoft.agents.client import (
    ChannelHostConfiguration,
    ChannelsConfiguration,
    ChannelInfo,
)


class DefaultConfig(MsalAuthConfiguration, ChannelsConfiguration):
    """Agent Configuration"""

    AUTH_TYPE = AuthTypes.client_secret
    TENANT_ID = ""
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    PORT = 3978
    SCOPES = ["https://api.botframework.com/.default"]

    # ChannelHost configuration
    @staticmethod
    def CHANNEL_HOST_CONFIGURATION():
        return ChannelHostConfiguration(
            CHANNELS=[
                ChannelInfo(
                    id="EchoAgent",
                    app_id="",  # Target agent's app_id
                    resource_url="http://localhost:3999/api/messages",
                    token_provider="ChannelConnection",
                    channel_factory="HttpAgentClient",
                    endpoint="http://localhost:3999/api/messages",
                )
            ],
            HOST_ENDPOINT="http://localhost:3978/api/botresponse/",
            HOST_APP_ID="",  # usually the same as CLIENT_ID
        )
