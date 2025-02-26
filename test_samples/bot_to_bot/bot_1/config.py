from microsoft.agents.authorization.msal import AuthTypes, MsalAuthConfiguration
from microsoft.agents.client import (
    ChannelHostConfiguration,
    ChannelsConfiguration,
    ChannelInfo,
)


class DefaultConfig(MsalAuthConfiguration, ChannelsConfiguration):
    """Bot Configuration"""

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
                    id="EchoBot",
                    app_id="",  # Target bot's app_id
                    resource_url="http://localhost:3999/api/messages",
                    token_provider="ChannelConnection",
                    channel_factory="HttpBotClient",
                    endpoint="http://localhost:3999/api/messages",
                )
            ],
            HOST_ENDPOINT="http://localhost:3978/api/botresponse/",
            HOST_APP_ID="",  # usually the same as CLIENT_ID
        )
