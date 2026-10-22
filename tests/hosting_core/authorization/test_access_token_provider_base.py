# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import subprocess
import sys


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
