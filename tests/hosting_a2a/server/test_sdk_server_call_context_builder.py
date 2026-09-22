# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from unittest.mock import MagicMock, patch

from a2a.auth.user import UnauthenticatedUser
from starlette.requests import Request

from microsoft_agents.hosting.core import ClaimsIdentity
from microsoft_agents.hosting.a2a.server._constants import _CLAIMS_IDENTITY_KEY
from microsoft_agents.hosting.a2a.server.sdk_server_call_context_builder import (
    SDKServerCallContextBuilder,
)


def _request(*, claims_identity=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/a2a",
        "raw_path": b"/a2a",
        "query_string": b"",
        "headers": [
            (b"x-a2a-extensions", b"extension-1"),
            (b"x-test", b"value"),
        ],
        "scheme": "https",
        "server": ("example.com", 443),
        "client": ("127.0.0.1", 1234),
        "state": {},
    }
    if claims_identity is not None:
        scope["state"]["claims_identity"] = claims_identity
    return Request(scope)


def test_build_copies_headers_extensions_and_claims_identity():
    identity = ClaimsIdentity({"sub": "agent-1"}, True)
    request = _request(claims_identity=identity)
    builder = SDKServerCallContextBuilder()
    user = UnauthenticatedUser()
    builder.build_user = MagicMock(return_value=user)

    with patch(
        "microsoft_agents.hosting.a2a.server."
        "sdk_server_call_context_builder.get_requested_extensions",
        return_value={"extension-1"},
    ) as get_extensions:
        context = builder.build(request)

    assert context.user is user
    assert context.state["headers"]["x-test"] == "value"
    assert context.state[_CLAIMS_IDENTITY_KEY] is identity
    assert context.requested_extensions == {"extension-1"}
    get_extensions.assert_called_once()


def test_build_omits_claims_identity_when_middleware_did_not_set_it():
    request = _request()
    builder = SDKServerCallContextBuilder()
    builder.build_user = MagicMock(return_value=UnauthenticatedUser())

    context = builder.build(request)

    assert _CLAIMS_IDENTITY_KEY not in context.state
