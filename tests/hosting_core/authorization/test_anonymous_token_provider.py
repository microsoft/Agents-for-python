# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import pytest
from azure.core.credentials import AccessToken

from microsoft_agents.hosting.core import AnonymousTokenProvider


@pytest.mark.asyncio
async def test_get_token_credential_is_synchronous():
    provider = AnonymousTokenProvider()

    credential = provider.get_token_credential()
    token = await credential.get_token("scope")

    assert token == AccessToken("", 2**31 - 1)
