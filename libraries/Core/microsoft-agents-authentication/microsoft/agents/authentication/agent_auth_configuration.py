from typing import Protocol, Optional


class AgentAuthConfiguration(Protocol):
    """
    Configuration for Agent authentication.
    """

    TENANT_ID: Optional[str]
    CLIENT_ID: Optional[str]

    @property
    def ISSUERS(self) -> list[str]:
        """
        Gets the list of issuers.
        """
        return [
            "https://api.botframework.com",
            f"https://sts.windows.net/{self.TENANT_ID}/",
            f"https://login.microsoftonline.com/{self.TENANT_ID}/v2.0",
        ]
