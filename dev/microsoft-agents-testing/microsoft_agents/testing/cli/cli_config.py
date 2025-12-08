import os
from dataclasses import dataclass

_UNSET = object()

def add_trailing_slash(url: str) -> str:
    """Add a trailing slash to the URL if it doesn't already have one."""
    if not url.endswith("/"):
        url += "/"
    return url

@dataclass
class _CLIConfig:
    """Configuration class for benchmark settings."""

    tenant_id: str = ""
    app_id: str = ""
    app_secret: str = ""
    _agent_url: str = "http://localhost:3978/"
    _service_url: str = "http://localhost:8001/"

    @property
    def service_url(self) -> str:
        """Return the service URL"""
        return self._service_url
    
    @service_url.setter
    def service_url(self, value: str) -> None:
        """Set the service URL"""
        self._service_url = add_trailing_slash(value)
    
    @property
    def agent_url(self) -> str:
        """Return the agent URL"""
        return self._agent_url
    
    @agent_url.setter
    def agent_url(self, value: str) -> None:
        """Set the agent URL"""
        self._agent_url = add_trailing_slash(value)

    @property
    def agent_endpoint(self) -> str:
        """Return the agent messaging endpoint"""
        return f"{self.agent_url}api/messages/"

    def load_from_config(self, config: dict | None = None) -> None:
        """Load configuration from a dictionary"""

        config = config or dict(os.environ)
        config = {key.upper(): value for key, value in config.items()}

        self.tenant_id = config.get("TENANT_ID", self.tenant_id)
        self.app_id = config.get("APP_ID", self.app_id)
        self.app_secret = config.get("APP_SECRET", self.app_secret)
        self.agent_url = config.get("AGENT_URL", self.agent_url)

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
