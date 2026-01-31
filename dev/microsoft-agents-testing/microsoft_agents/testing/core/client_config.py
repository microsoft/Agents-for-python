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
    
    # Identity (for multi-user scenarios)
    user_id: str = "user-id"
    user_name: str = "User"
    
    def with_headers(self, **headers: str) -> ClientConfig:
        """Return a new config with additional headers."""
        new_headers = {**self.headers, **headers}
        return ClientConfig(
            headers=new_headers,
            auth_token=self.auth_token,
            activity_template=self.activity_template,
            user_id=self.user_id,
            user_name=self.user_name,
        )
    
    def with_auth(self, token: str) -> ClientConfig:
        """Return a new config with a specific auth token."""
        return ClientConfig(
            headers=self.headers,
            auth_token=token,
            activity_template=self.activity_template,
            user_id=self.user_id,
            user_name=self.user_name,
        )
    
    def with_user(self, user_id: str, user_name: str | None = None) -> ClientConfig:
        """Return a new config for a different user identity."""
        return ClientConfig(
            headers=self.headers,
            auth_token=self.auth_token,
            activity_template=self.activity_template,
            user_id=user_id,
            user_name=user_name or user_id,
        )
    
    def with_template(self, template: ActivityTemplate) -> ClientConfig:
        """Return a new config with a specific activity template."""
        return ClientConfig(
            headers=self.headers,
            auth_token=self.auth_token,
            activity_template=template,
            user_id=self.user_id,
            user_name=self.user_name,
        )