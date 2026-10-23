# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import subprocess
import sys

import pytest

from microsoft_agents.hosting.core import (
    AccessTokenProviderBase,
    AgentAuthConfiguration,
)
from microsoft_agents.hosting.core.authorization.connections import (
    ConnectionSettingsBase,
)


def test_authorization_imports_without_circular_dependency():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from microsoft_agents.hosting.core.authorization "
            "import AccessTokenProviderBase; "
            "from microsoft_agents.hosting.core.authorization.connections "
            "import ConnectionSettingsBase; "
            "from microsoft_agents.authentication.msal import MsalConnectionManager",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_legacy_provider_subclasses_can_use_the_default_config_binding():
    with pytest.warns(DeprecationWarning, match="AgentAuthConfiguration"):
        legacy = AgentAuthConfiguration(
            client_id="legacy-client",
            tenant_id="tenant",
            ALT_BLUEPRINT_NAME="blueprint",
            CUSTOM_SETTING="extra",
        )

    class LegacyProvider(AccessTokenProviderBase):
        @property
        def configuration(self):
            return legacy

        async def get_access_token(self, resource_url, scopes, force_refresh=False):
            return "token"

        def get_token_credential(self):
            raise NotImplementedError()

    settings = LegacyProvider().config

    assert isinstance(settings, ConnectionSettingsBase)
    assert settings.client_id == "legacy-client"
    assert settings.tenant_id == "tenant"
    assert settings.alternate_blueprint_connection_name == "blueprint"
    assert settings.extras["CUSTOM_SETTING"] == "extra"
