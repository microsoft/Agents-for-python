# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

"""Configuration classes for agent testing scenarios.

Provides dataclasses for configuring both scenario-level and client-level
settings used throughout the testing framework.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .fluent import ActivityTemplate


@dataclass
class ClientConfig:
    """Configuration for creating an AgentClient.
    
    This immutable configuration class uses a builder pattern - each `with_*`
    method returns a new instance with the updated value.
    
    Example::
    
        config = ClientConfig()
            .with_auth_token("my-token")
            .with_headers(X_Custom="value")
    """
    
    # HTTP configuration
    headers: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None
    
    # Activity defaults
    activity_template: ActivityTemplate | None = None
    
    def with_headers(self, **headers: str) -> ClientConfig:
        """Return a new config with additional headers merged into existing ones.

        :param headers: Keyword arguments of header name-value pairs.
        :return: A new ClientConfig with the merged headers.
        """
        new_headers = {**self.headers, **headers}
        return ClientConfig(
            headers=new_headers,
            auth_token=self.auth_token,
            activity_template=self.activity_template,
        )
    
    def with_auth_token(self, token: str) -> ClientConfig:
        """Return a new config with a specific auth token.

        :param token: The Bearer token to use for authentication.
        :return: A new ClientConfig with the specified auth token.
        """
        return ClientConfig(
            headers=self.headers,
            auth_token=token,
            activity_template=self.activity_template,

        )
    
    def with_template(self, template: ActivityTemplate) -> ClientConfig:
        """Return a new config with a specific activity template.

        :param template: The ActivityTemplate to apply to outgoing activities.
        :return: A new ClientConfig with the specified template.
        """
        return ClientConfig(
            headers=self.headers,
            auth_token=self.auth_token,
            activity_template=template,
        )
    
@dataclass
class ScenarioConfig:
    """Configuration for agent test scenarios.
    
    Controls scenario-level settings such as environment file location,
    callback server port, and default client configuration.
    
    Attributes:
        env_file_path: Path to a .env file for loading environment variables.
        callback_server_port: Port for the callback server to receive agent responses.
        client_config: Default ClientConfig for clients created in this scenario.
    """
    env_file_path: str | None = None
    callback_server_port: int = 9378
    client_config: ClientConfig = field(default_factory=ClientConfig)