# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations
from dataclasses import dataclass, field

from .fluent import ActivityTemplate

@dataclass
class ClientConfig:
    """Configuration for creating an AgentClient."""
    
    # HTTP configuration
    headers: dict[str, str] = field(default_factory=dict)
    auth_token: str | None = None
    
    # Activity defaults
    activity_template: ActivityTemplate | None = None
    
    def with_headers(self, **headers: str) -> ClientConfig:
        """Return a new config with additional headers."""
        new_headers = {**self.headers, **headers}
        return ClientConfig(
            headers=new_headers,
            auth_token=self.auth_token,
            activity_template=self.activity_template,
        )
    
    def with_auth_token(self, token: str) -> ClientConfig:
        """Return a new config with a specific auth token."""
        return ClientConfig(
            headers=self.headers,
            auth_token=token,
            activity_template=self.activity_template,

        )
    
    def with_template(self, template: ActivityTemplate) -> ClientConfig:
        """Return a new config with a specific activity template."""
        return ClientConfig(
            headers=self.headers,
            auth_token=self.auth_token,
            activity_template=template,
        )
    
@dataclass
class ScenarioConfig:
    """Configuration for agent test scenarios."""
    env_file_path: str | None = None
    callback_server_port: int = 9378
    client_config: ClientConfig = field(default_factory=ClientConfig)