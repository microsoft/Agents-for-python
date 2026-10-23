# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from a2a.auth.user import UnauthenticatedUser
from starlette.requests import Request

from microsoft_agents.hosting.core import ClaimsIdentity
from microsoft_agents.hosting.a2a.server._constants import _CLAIMS_IDENTITY_KEY
from microsoft_agents.hosting.a2a.server.sdk_server_call_context_builder import (
    SDKServerCallContextBuilder,
)


def _request(*, claims_identity=None, auth=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/a2a",
        "raw_path": b"/a2a",
        "query_string": b"",
        "headers": [
            (b"a2a-extensions", b"extension-1"),
            (b"x-test", b"value"),
        ],
        "scheme": "https",
        "server": ("example.com", 443),
        "client": ("127.0.0.1", 1234),
        "state": {},
    }
    if claims_identity is not None:
        scope["state"]["claims_identity"] = claims_identity
    if auth is not None:
        scope["auth"] = auth
    return Request(scope)


def test_build_copies_headers_extensions_and_claims_identity():
    identity = ClaimsIdentity({"sub": "agent-1"}, True)
    request = _request(claims_identity=identity)
    builder = SDKServerCallContextBuilder()

    context = builder.build(request)

    assert isinstance(context.user, UnauthenticatedUser)
    assert context.state["headers"]["x-test"] == "value"
    assert context.state[_CLAIMS_IDENTITY_KEY] is identity
    assert context.requested_extensions == {"extension-1"}


def test_build_omits_claims_identity_when_middleware_did_not_set_it():
    request = _request()
    builder = SDKServerCallContextBuilder()

    context = builder.build(request)

    assert isinstance(context.user, UnauthenticatedUser)
    assert _CLAIMS_IDENTITY_KEY not in context.state


def test_build_copies_asgi_auth_scope():
    auth = object()
    request = _request(auth=auth)
    builder = SDKServerCallContextBuilder()

    context = builder.build(request)

    assert context.state["auth"] is auth
