# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from enum import Enum, auto


from microsoft_agents.hosting.core import AgentAuthConfiguration

class A2AUserAuthorizationMode(str, Enum):
    """Enumeration for A2A user authorization modes."""
    IN_TASK = auto(),
    REQUEST_TOKEN = auto()

class A2AUserAuthorizationSettings:
    """Settings for A2A user authorization."""

    mode: A2AUserAuthorizationMode
    security_scheme_name: str
    required_scopes: list[str]
    enforce_required_scopes: bool

    def __init__(self, config: AgentAuthConfiguration) -> None:
    
            self._config = config

    @staticmethod
    def from_config(config: AgentAuthConfiguration) -> A2AUserAuthorizationSettings:
        return A2AUserAuthorizationSettings(
            
        )