import os
from dataclasses import dataclass

_UNSET = object()


@dataclass
class _CLIConfig:
    """Configuration class for benchmark settings."""

    tenant_id: str = ""
    app_id: str = ""
    app_secret: str = ""
    agent_endpoint: str = "http://localhost:3978/api/messages"

    def load_from_config(self, config: dict | None = None) -> None:
        """Load configuration from a dictionary"""

        config = config or dict(os.environ)

        self.tenant_id = config.get("tenant_id", self.tenant_id)
        self.app_id = config.get("app_id", self.app_id)
        self.app_secret = config.get("app_secret", self.app_secret)
        self.agent_endpoint = config.get("agent_endpoint", self.agent_endpoint)

    def load_from_connection(
        self, connection_name: str = "SERVICE_CONNECTION", config: dict | None = None
    ) -> None:
        """Load configuration from a connection dictionary."""

        config = config or dict(os.environ)

        config = {
            "app_id": os.environ.get(
                f"CONNECTIONS__{connection_name}__SETTINGS__CLIENTID", _UNSET
            ),
            "app_secret": os.environ.get(
                f"CONNECTIONS__{connection_name}__SETTINGS__CLIENTSECRET", _UNSET
            ),
            "tenant_id": os.environ.get(
                f"CONNECTIONS__{connection_name}__SETTINGS__TENANTID", _UNSET
            ),
        }

        config = {key: value for key, value in config.items() if value is not _UNSET}

        self.load_from_config(config)


cli_config = _CLIConfig()
cli_config.load_from_config()
